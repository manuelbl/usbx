# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from enum import IntEnum


class TransferType(IntEnum):
    """USB transfer type."""

    CONTROL = 0
    """Control transfer."""

    ISOCHRONOUS = 1
    """Isochronous transfer."""

    BULK = 2
    """Bulk transfer."""

    INTERRUPT = 3
    """Interrupt transfer."""

    @classmethod
    def from_attributes(cls, attributes: int) -> 'TransferType':
        """Extract the transfer type from ``bmAttributes`` of an endpoint descriptor."""
        return TransferType(attributes & 0x03)


class TransferDirection(IntEnum):
    """USB transfer direction."""

    OUT = 0
    """Direction out (host to device)."""

    IN = 1
    """Direction in (device to host)."""

    @classmethod
    def from_address(cls, address: int) -> 'TransferDirection':
        """Extract the transfer direction from an endpoint address."""
        return TransferDirection.OUT if (address & 0x80) == 0 else TransferDirection.IN


class RequestType(IntEnum):
    """USB control request type."""

    STANDARD = 0
    """Standard request."""

    CLASS = 1
    """USB class specific request."""

    VENDOR = 2
    """Vendor specific request."""


class Recipient(IntEnum):
    """USB control request recipient."""

    DEVICE = 0
    """Control request to device."""

    INTERFACE = 1
    """Control request to interface."""

    ENDPOINT = 2
    """Control request to endpoint."""

    OTHER = 3
    """Other recipient for control request."""
