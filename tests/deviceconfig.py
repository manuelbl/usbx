# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from dataclasses import dataclass
from typing import Optional

from usbx import Device


@dataclass
class TestDeviceConfig:
    """Test device configuration"""

    vid: int
    """Vendor ID"""

    pid: int
    """Product ID"""

    is_composite: bool
    """Indicates if this devices is the composite device"""

    interface_number: int
    """Interface number for loopback and echo endpoints"""

    endpoint_loopback_out: int
    """Loopback OUT endpoint number"""

    endpoint_loopback_in: int
    """Loopback IN endpoint number"""

    endpoint_echo_out: int
    """Echo OUT endpoint number"""

    endpoint_echo_in: int
    """Echo IN endpoint number"""


LOOPBACK_DEVICE = TestDeviceConfig(
    0xcafe,
    0xceaf,
    False,
    0,
    1,
    2,
    3,
    3
)

COMPOSITE_DEVICE = TestDeviceConfig(
    0xcafe,
    0xcea0,
    True,
    3,
    1,
    2,
    -1,
    -1
)


def get_config(device: Device) -> Optional[TestDeviceConfig]:
    """
    Gets the test device configuration for the specified USB device.

    :param device: The USB device.
    :return: The test device configuration (:class:`TestDeviceConfig` instance) or ``None``
    """
    return next((c for c in [LOOPBACK_DEVICE, COMPOSITE_DEVICE] if device.vid == c.vid and device.pid == c.pid), None)
