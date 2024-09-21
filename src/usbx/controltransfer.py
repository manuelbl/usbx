# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from dataclasses import dataclass

from .enums import RequestType, Recipient


@dataclass
class ControlTransfer:
    """USB control transfer request."""

    request_type: RequestType
    """Request type (bits 5 and 6 of ``bmRequestType``)."""

    recipient: Recipient
    """Recipient of request (bits 0 to 4 of ``bmRecipient``)."""

    request: int
    """Request code (value between 0 and 255, called ``bRequest`` in USB specification)."""

    value: int
    """Value (value between 0 and 65535, called ``wValue`` in USB specification)."""

    index: int
    """
    Index (value between 0 and 65535, called ``wIndex`` in USB specification).
    
    For requests with an interface or an endpoint as the recipient, the lower
    byte of this property must contain the interface number and the endpoint address, respectively.
    """
