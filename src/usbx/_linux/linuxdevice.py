# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import errno
import fcntl
import logging
import os
from ctypes import c_uint
from typing import Optional

from .asynctransfer import async_dispatcher, Transfer
from .usbdevfs import CtrlTransfer, USBDEVFS_CLAIMINTERFACE, USBDEVFS_RELEASEINTERFACE, USBDEVFS_CONTROL, \
    USBDEVFS_SETINTERFACE, SetInterface, USBDEVFS_CLEAR_HALT, DisconnectClaim, USBDEVFS_DISCONNECT_CLAIM_EXCEPT_DRIVER, \
    USBDEVFS_DISCONNECT_CLAIM, IoCtl, USBDEVFS_CONNECT, USBDEVFS_IOCTL
from .. import TransferType
from ..exceptions import USBError, StallError, TransferTimeoutError
from ..enums import TransferDirection
from ..controltransfer import ControlTransfer
from ..configuration import Endpoint
from .._common.ctypesfunc import writable_buffer, readable_buffer
from .._common.devicebase import DeviceBase


def create_ctrl_transfer(transfer: ControlTransfer, direction: TransferDirection) -> CtrlTransfer:
    bm_request = ((0x80 if direction == TransferDirection.IN else 0x00) | (transfer.request_type.value << 5) |
                  transfer.recipient.value)
    return CtrlTransfer(bm_request, transfer.request, transfer.value, transfer.index)


def convert_to_usb_exception(err: OSError, operation: str) -> USBError:
    if isinstance(err, TimeoutError):
        return TransferTimeoutError(f'{operation} timed out')
    if isinstance(err, BrokenPipeError):
        return StallError(f'{operation} stalled')
    return USBError(f'{operation} failed')


class LinuxDevice(DeviceBase):
    def __init__(self, path: str):
        super().__init__(path)

        self.device_fd: int = -1
        self.detach_drivers: bool = False

        with open(path, mode='rb') as file:  # b is important -> binary
            descriptors = file.read()

        # `descriptors` contains the device descriptor followed by the configuration descriptor
        # (including the interface descriptors, endpoint descriptors etc.)
        self.set_descriptors(descriptors[:18], descriptors[18:])

    def open(self) -> None:
        with self._device_lock:
            self.check_is_closed_and_connected()
            path = self.identifier.encode('utf-8')
            try:
                self.device_fd = os.open(path, os.O_RDWR | os.O_CLOEXEC)
            except OSError as exc:
                raise convert_to_usb_exception(exc, f'opening device {self.identifier}') from exc
            self.is_open = True
            async_dispatcher.add_device(self.device_fd)

    def close(self) -> None:
        with self._device_lock:
            if not self.is_open:
                return

            async_dispatcher.remove_device(self.device_fd)

            try:
                os.close(self.device_fd)
            except OSError as exc:
                logging.warning(f'failed to close device {self.identifier} ({exc})')

            self.is_open = False
            self.device_fd = 0
            for intf in self.configuration.interfaces:
                self.set_claimed(intf.number, False)

    def claim_interface(self, number: int) -> None:
        with self._device_lock:
            self.check_is_open()
            self.get_and_check_interface(number, False)

            if self.detach_drivers:
                disconnect_claim = DisconnectClaim(number, USBDEVFS_DISCONNECT_CLAIM_EXCEPT_DRIVER)
                disconnect_claim.driver = b'usbfs'
                try:
                    fcntl.ioctl(self.device_fd, USBDEVFS_DISCONNECT_CLAIM, disconnect_claim)
                except OSError as exc:
                    raise convert_to_usb_exception(exc, f'disconnecting driver and claiming interface {number}') from exc

            else:
                intf_number = c_uint(number)
                try:
                    fcntl.ioctl(self.device_fd, USBDEVFS_CLAIMINTERFACE, intf_number)
                except OSError as exc:
                    raise convert_to_usb_exception(exc, f'claiming interface {number}') from exc

            self.set_claimed(number, True)

    def release_interface(self, number: int) -> None:
        with self._device_lock:
            self.check_is_open()
            self.get_and_check_interface(number, True)

            try:
                intf_number = c_uint(number)
                fcntl.ioctl(self.device_fd, USBDEVFS_RELEASEINTERFACE, intf_number)
            except OSError as exc:
                raise convert_to_usb_exception(exc, f'releasing interface {number}') from exc

            self.set_claimed(number, False)

            if self.detach_drivers:
                cmd = IoCtl(number, USBDEVFS_CONNECT, None)
                try:
                    fcntl.ioctl(self.device_fd, USBDEVFS_IOCTL, cmd)
                except OSError as exc:
                    raise convert_to_usb_exception(exc, f'connecting standard driver to interface {number}') from exc

    def select_alternate(self, interface_number: int, alternate_number: int) -> None:
        with self._device_lock:
            self.check_alternate_interface(interface_number, alternate_number)

            try:
                set_interface = SetInterface(interface_number, alternate_number)
                fcntl.ioctl(self.device_fd, USBDEVFS_SETINTERFACE, set_interface)
            except OSError as exc:
                raise convert_to_usb_exception(exc, f'setting interface {interface_number} to alternate {alternate_number}') from exc

            self.set_current_alternate(interface_number, alternate_number)

    def control_transfer_in(self, transfer: ControlTransfer, length: int) -> bytes:
        with self._device_lock:
            self.check_control_transfer(transfer, TransferDirection.IN)
            fd = self.device_fd

        ctrl_transfer = create_ctrl_transfer(transfer, TransferDirection.IN)
        ctrl_transfer.wLength = length
        buffer = bytearray(length)
        ctrl_transfer.data = writable_buffer(buffer)
        try:
            transferred = fcntl.ioctl(fd, USBDEVFS_CONTROL, ctrl_transfer, True)
        except OSError as exc:
            raise convert_to_usb_exception(exc, 'control transfer IN') from exc

        return bytes(buffer[:transferred])

    def control_transfer_out(self, transfer: ControlTransfer, data: bytes = None) -> None:
        with self._device_lock:
            self.check_control_transfer(transfer, TransferDirection.OUT)
            fd = self.device_fd

        ctrl_transfer = create_ctrl_transfer(transfer, TransferDirection.OUT)
        if data is not None:
            ctrl_transfer.wLength = len(data)
            ctrl_transfer.data = readable_buffer(data)
        try:
            fcntl.ioctl(fd, USBDEVFS_CONTROL, ctrl_transfer)
        except OSError as exc:
            raise convert_to_usb_exception(exc, 'control transfer OUT') from exc

    def transfer_in(self, endpoint_number: int, timeout: Optional[float] = None) -> bytes:
        with self._device_lock:
            endpoint, _ = self.get_and_check_endpoint_and_interface(endpoint_number, TransferDirection.IN)
            buffer = bytearray(endpoint.max_packet_size)
            address = Endpoint.get_address(endpoint_number, TransferDirection.IN)
            transfer = async_dispatcher.submit_transfer(self.device_fd, address, TransferType.BULK, buffer, len(buffer))

        self.wait_for_transfer(transfer, timeout, endpoint_number, TransferDirection.IN)
        return bytes(buffer[:transfer.result_size])

    def transfer_out(self, endpoint_number: int, data: bytes, timeout: Optional[float] = None) -> None:
        with self._device_lock:
            _, _ = self.get_and_check_endpoint_and_interface(endpoint_number, TransferDirection.OUT)
            address = Endpoint.get_address(endpoint_number, TransferDirection.OUT)
            transfer = async_dispatcher.submit_transfer(self.device_fd, address, TransferType.BULK, data, len(data))

        self.wait_for_transfer(transfer, timeout, endpoint_number, TransferDirection.OUT)

    def clear_halt(self, number: int, direction: TransferDirection) -> None:
        with self._device_lock:
            _, _ = self.get_and_check_endpoint_and_interface(number, direction)
            address = c_uint(Endpoint.get_address(number, direction))
            fd = self.device_fd

        try:
            fcntl.ioctl(fd, USBDEVFS_CLEAR_HALT, address)
        except OSError as exc:
            raise convert_to_usb_exception(exc, f'clearing halt for endpoint {number}/{direction.name}') from exc

    def abort_transfers(self, number: int, direction: TransferDirection) -> None:
        with self._device_lock:
            _, _ = self.get_and_check_endpoint_and_interface(number, direction)
            address = Endpoint.get_address(number, direction)
            fd = self.device_fd

        async_dispatcher.abort_transfers(fd, address)

    def wait_for_transfer(self, transfer: Transfer, timeout: float, endpoint_number: int,
                          direction: TransferDirection) -> None:
        if timeout is None:
            transfer.event.wait()
        else:
            flag = transfer.event.wait(timeout)
            if not flag and transfer.result_code == 0:
                address = Endpoint.get_address(endpoint_number, direction)
                async_dispatcher.abort_transfers(self.device_fd, address)
                transfer.event.wait()
                raise TransferTimeoutError('transfer timed out')

        if transfer.result_code != 0:
            if transfer.result_code == errno.EPIPE:
                raise StallError('transfer stalled')

            msg = os.strerror(transfer.result_code)
            raise USBError(f'transfer failed - {msg}')

    def detach_standard_drivers(self) -> None:
        self.check_is_closed_and_connected()
        self.detach_drivers = True

    def attach_standard_drivers(self) -> None:
        self.check_is_closed_and_connected()
        self.detach_drivers = False
