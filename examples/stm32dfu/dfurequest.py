# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from enum import IntEnum


class DFURequest(IntEnum):
    """
    DFU request.
    
    See USB Device Class Specification for Device Firmware Upgrade, version 1.1.
    """
    DETACH = 0
    DOWNLOAD = 1
    UPLOAD = 2
    GET_STATUS = 3
    CLEAR_STATUS = 4
    GET_STATE = 5
    ABORT = 6
