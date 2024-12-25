# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from enum import IntEnum


class DeviceState(IntEnum):
    """
    Device state.
    
    See USB Device Class Specification for Device Firmware Upgrade, version 1.1
    """
    
    APP_IDLE = 0
    """Device is running its normal application"""

    APP_DETACH = 1
    """Device is running its normal application, has received the DFU_DETACH request,
    and is waiting for a USB reset."""
    
    DFU_IDLE = 2
    """Device is operating in the DFU mode and is waiting for requests."""

    DFU_DNLOAD_SYNC = 3
    """Device has received a block and is waiting for the host to solicit the status via DFU_GETSTATUS."""

    DFU_DNBUSY = 4
    """Device is programming a control-write block into its nonvolatile memories."""

    DFU_DNLOAD_IDLE = 5
    """Device is processing a download operation. Expecting DFU_DNLOAD requests."""

    DFU_MANIFEST_SYNC = 6
    """Device has received the final block of firmware from the host and is waiting for receipt of
    DFU_GETSTATUS to begin the Manifestation phase; or device has completed the Manifestation phase and is
    waiting for receipt of DFU_GETSTATUS. (Devices that can enter this state after the Manifestation phase
    set bmAttributes bit bitManifestationTolerant to 1.)"""
    
    DFU_MANIFEST = 7
    """Device is in the Manifestation phase. (Not all devices will be able to respond to DFU_GETSTATUS
    when in this state."""

    DFU_MANIFEST_WAIT_RESET = 8
    """Device has programmed its memories and is waiting for a USB reset or a power on reset.
    (Devices that must enter this state clear bitManifestationTolerant to 0.)"""

    DFU_UPLOAD_IDLE = 9
    """The device is processing an upload operation. Expecting DFU_UPLOAD requests."""

    DFU_ERROR = 10
    """An error has occurred. Awaiting the DFU_CLRSTATUS request."""
