# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from ctypes import FormatError, get_last_error

from .. import USBError, StallError
from ..exceptions import TransferTimeoutError

ERROR_SEM_TIMEOUT = 121

ERROR_GEN_FAILURE = 31


def raise_error(error_code: int, msg: str) -> None:
    err_msg = FormatError(error_code)
    raise WindowsError(
        error_code,
        f'{msg} - {err_msg}',
    )


def raise_last_error(msg: str) -> None:
    raise_error(get_last_error(), msg)


def raise_last_usb_error(msg: str) -> None:
    error_code = get_last_error()
    if error_code == ERROR_SEM_TIMEOUT:
        raise TransferTimeoutError('transfer timed out')

    if error_code == ERROR_GEN_FAILURE:
        raise StallError('endpoint has stalled')

    err_msg = FormatError(error_code)
    raise USBError(f'{msg} - {err_msg}')
