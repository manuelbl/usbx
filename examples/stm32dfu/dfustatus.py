# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from dataclasses import dataclass
import struct
from devicestate import DeviceState
from devicestatus import DeviceStatus


@dataclass
class DFUStatus:
    """
    DFU GET_STATUS response
    
    See USB Device Class Specification for Device Firmware Upgrade, version 1.1
    """

    status: DeviceStatus
    """An indication of the status resulting from the execution of the most recent request. """

    poll_timeout: float
    """Minimum time, in seconds, that the host should wait before sending a subsequent DFU_GETSTATUS request."""

    state: DeviceState
    """An indication of the state that the device is going to enter immediately following transmission of this response"""

    @staticmethod
    def from_bytes(data: bytes) -> 'DFUStatus':
        return DFUStatus(
            status = DeviceStatus(data[0]),
            poll_timeout = struct.unpack('<I', data[1:4] + b'\0')[0] / 1000,
            state = DeviceState(data[4])
        )
