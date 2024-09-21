# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

class USBError(Exception):
    """
    Exception raised when a USB operation fails.
    """
    def __init__(self, message: str):
        super().__init__(message)


class StallError(USBError):
    """
    Exception raised when a USB endpoint stalls.

    Stalling is an endpoint's way to indicate an error has occurred
    such as an invalid packet that has been received.

    A stalled endpoint is halted and must be reactivated by
    clearing the halt using :meth:`Device.clear_halt`.
    The exception is control endpoint 0, which clears the halt condition automatically.
    """
    def __init__(self, message: str):
        super().__init__(message)


class TransferTimeoutError(USBError):
    """
    Exception raised when a USB transfer times out.
    """
    def __init__(self, message: str):
        super().__init__(message)
