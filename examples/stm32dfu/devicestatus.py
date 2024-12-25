# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from enum import IntEnum


class DeviceStatus(IntEnum):
    """
    DFU device status.
    
    See USB Device Class Specification for Device Firmware Upgrade, version 1.1.
    """

    OK = 0
    """No error condition is present"""

    ERR_TARGET = 1
    """File is not targeted for use by this device."""

    ERR_FILE = 2
    """File is for this device but fails some vendor-specific verification test."""

    ERR_WRITE = 3
    """Device is unable to write memory."""

    ERR_ERASE = 4
    """Memory erase function failed."""

    ERR_CHECK_ERASED = 5
    """Memory erase check failed."""

    ERR_PROG = 6
    """Program memory function failed."""

    ERR_VERIFY = 7
    """Programmed memory failed verification."""

    ERR_ADDRESS = 8
    """Cannot program memory due to received address that is out of range."""

    ERR_NOTDONE = 9
    """Received DFU_DNLOAD with wLength = 0, but device does not think it has all of the data yet."""

    ERR_FIRMWARE = 10
    """Device's firmware is corrupt. It cannot return to run-time (non-DFU) operations."""

    ERR_VENDOR = 11
    """iString indicates a vendor-specific error."""

    ERR_USBR = 12
    """Device detected unexpected USB reset signaling."""

    ERR_POR = 13
    """Device detected unexpected power on reset."""

    ERR_UNKNOWN = 14
    """Something went wrong, but the device does not know what it was."""

    ERR_STALLEDPKT = 15
    """Device stalled an unexpected request."""
