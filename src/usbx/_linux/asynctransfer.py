# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT
from __future__ import annotations

import errno
import os
from select import epoll, EPOLLOUT
from ctypes import c_void_p, addressof, byref, c_ulong, c_int, CDLL, get_errno
from threading import Event, Lock, Thread
from typing import Optional, Union

from .usbdevfs import Urb, USBDEVFS_REAPURBNDELAY, USBDEVFS_URB_TYPE_BULK, USBDEVFS_URB_TYPE_INTERRUPT, \
    USBDEVFS_URB_TYPE_ISO, USBDEVFS_URB_TYPE_CONTROL, USBDEVFS_SUBMITURB, USBDEVFS_DISCARDURB
from .. import USBError
from ..configuration import Endpoint
from ..enums import TransferType, TransferDirection
from .._common.ctypesfunc import readable_buffer, writable_buffer


libc = CDLL('libc.so.6', use_errno = True)
libc.ioctl.arg_types = [c_int, c_ulong, c_void_p]
libc.ioctl.restype = c_int


def urb_transfer_type(transfer_type: TransferType) -> int:
    if transfer_type == TransferType.BULK:
        return USBDEVFS_URB_TYPE_BULK
    if transfer_type == TransferType.INTERRUPT:
        return USBDEVFS_URB_TYPE_INTERRUPT
    if transfer_type == TransferType.CONTROL:
        return USBDEVFS_URB_TYPE_CONTROL
    return USBDEVFS_URB_TYPE_ISO


class Transfer(object):
    def __init__(self):
        self.device_fd: int = 0
        self.result_code: int = 0
        self.result_size: int = 0
        self.urb: Optional[Urb] = Urb()
        self.event: Event = Event()

class AsyncTask(object):
    def __init__(self):
        self.lock: Lock = Lock()
        self.epoll: Optional[epoll] = None
        self.transfers: dict[int, Transfer] = {}
        self.bg_thread: Optional[Thread] = None

    def add_device(self, fd: int) -> None:
        with self.lock:
            if self.epoll is None:
                self.start_background_thread()
            self.epoll.register(fd, EPOLLOUT)

    def remove_device(self, fd: int) -> None:
        with self.lock:
            try:
                self.epoll.unregister(fd)

                # reap outstanding URBs
                self.reap_urb(fd)
            except FileNotFoundError:
                pass  # ignore; it occurs if device has been unplugged

            # release outstanding transfers
            keys = set()
            for key, transfer in self.transfers.items():
                if transfer.device_fd == fd:
                    transfer.result_code = errno.ENODEV
                    transfer.result_size = 0
                    transfer.urb = None
                    transfer.event.set()
                    keys.add(key)

            if len(keys) > 0:
                self.transfers = { k: v for k, v in self.transfers.items() if k not in keys }

    def submit_transfer(self, device_fd: int, endpoint_address: int, transfer_type: TransferType,
                        data: Union[bytes | bytearray], data_size: int) -> Transfer:
        """
        Submit a transfer to the device.

        Once the transfer is completed (or has failed), the ``event`` is set.
        """
        with self.lock:
            direction = Endpoint.get_direction(endpoint_address)

            urb = Urb()
            urb.type = urb_transfer_type(transfer_type)
            urb.endpoint = endpoint_address
            urb.buffer = readable_buffer(data) if direction == TransferDirection.OUT else writable_buffer(data)
            urb.buffer_length = data_size

            transfer = Transfer()
            transfer.device_fd = device_fd
            transfer.data_size = data_size
            transfer.event = Event()
            transfer.urb = urb

            self.transfers[addressof(urb)] = transfer

            # Use custom ioctl() as fcntl.ioctl does not accept pointers as the third argument
            # and copies structs (changing the address).
            res = libc.ioctl(device_fd, USBDEVFS_SUBMITURB, byref(urb))
            if res != 0:
                raise USBError(f'internal error submitting URB - {os.strerror(get_errno())}')
            return transfer

    def abort_transfers(self, device_fd: int, endpoint_address: int) -> None:
        """Aborts the transfers on ``endpoint_address`` for ``device_fd``."""
        with self.lock:
            for transfer in self.transfers.values():
                urb = transfer.urb
                if transfer.device_fd == device_fd and urb.endpoint == endpoint_address:
                    res = libc.ioctl(device_fd, USBDEVFS_DISCARDURB, byref(urb))
                    if res != 0:
                        err = get_errno()
                        # ignore EINVAL; it occurs if the URB has completed at the same time
                        if err != errno.EINVAL:
                            raise USBError(f'internal error aborting transfer - {os.strerror(err)}')

    def completion_task(self) -> None:
        """Background task handling completion of asynchronous USB requests"""
        while True:
            events = self.epoll.poll()
            with self.lock:
                for fd, _ in events:
                    self.reap_urb(fd)

    def reap_urb(self, fd: int) -> None:
        """
        Reap all pending URBs for file descriptor ``fd``
        and handle the completed transfer.
        """
        urb_ptr = c_void_p()
        while True:
            # Use custom ioctl() to be able to pass a pointer.
            res = libc.ioctl(fd, USBDEVFS_REAPURBNDELAY, byref(urb_ptr))
            if res != 0:
                err = get_errno()
                if err == errno.EAGAIN:
                    return  # no more URBs to reap
                if err == errno.ENODEV:
                    self.epoll.unregister(fd)
                    return  # device has likely been closed
                raise OSError(err, os.strerror(err))

            transfer = self.transfers.pop(urb_ptr.value)
            urb = transfer.urb
            transfer.result_code = -urb.status
            transfer.result_size = urb.actual_length
            transfer.urb = None
            transfer.event.set()

    def start_background_thread(self) -> None:
        self.epoll = epoll()
        self.bg_thread = Thread(target=self.completion_task, daemon=True)
        self.bg_thread.start()


async_dispatcher: AsyncTask = AsyncTask()
