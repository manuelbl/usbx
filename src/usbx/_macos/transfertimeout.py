# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from threading import Timer, Lock
from typing import Optional

from .iokit import IOUSBInterfaceHandle
from .macoserrors import check_result


class TransferTimeout(object):
    """
    Schedules a timeout for the specified endpoint.

    If the timeout expires, the transfer is aborted.
    """

    def __init__(self, timeout: int, intf_handle: IOUSBInterfaceHandle, pipe_index: int):
        """
        :param timeout: Timeout in milliseconds.
        :param intf_handle: Interface handle.
        :param pipe_index: Endpoint index.
        """
        self.lock: Lock = Lock()
        self.intf_handle: IOUSBInterfaceHandle = intf_handle
        intf_handle.contents.contents.AddRef(intf_handle)
        self.pipe_index: int = pipe_index
        self.timer: Optional[Timer] = Timer(timeout / 1000.0, self.abort)
        self.timer.daemon = True
        self.timer.start()

    def cancel(self) -> None:
        """
        Cancels the timeout.
        """
        with self.lock:
            self.timer.cancel()
            self.timer = None
            self.intf_handle.contents.contents.Release(self.intf_handle)

    def abort(self) -> None:
        """
        Aborts the timeout.
        """
        with self.lock:
            if self.timer is None:
                return
            self.timer = None
            result = self.intf_handle.contents.contents.AbortPipe(self.intf_handle, self.pipe_index)
            self.intf_handle.contents.contents.Release(self.intf_handle)
            check_result(result, 'Error aborting endpoint transfer')
