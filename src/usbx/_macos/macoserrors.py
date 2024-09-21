# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from .corefoundation import mach_error_message
from .iokit import kern_return_t, kIOUSBPipeStalled, kIOUSBTransactionTimeout
from ..exceptions import StallError, TransferTimeoutError, USBError


def check_result(result: kern_return_t, message: str) -> None:
    """
    Checks the results and raises an exception if the result is not ok
    :param result: the result code
    :param message: the error message
    :raise StallError: if the endpoint has stalled
    :raise TransferTimeoutError: if the transfer has timed out
    :raise USBError: for any other error
    """
    if result == 0:
        return

    if result == kIOUSBPipeStalled:
        raise StallError('endpoint has stalled')
    elif result == kIOUSBTransactionTimeout:
        raise TransferTimeoutError('transfer timed out')
    else:
        msg = mach_error_message(result)
        raise USBError(f'{message} – {msg} ({result:08x})')
