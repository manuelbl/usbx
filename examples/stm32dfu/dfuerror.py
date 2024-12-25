# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

class DFUError(Exception):
    """
    Exception raised when a DFU operation fails.
    """

    def __init__(self, message: str):
        super().__init__(message)
