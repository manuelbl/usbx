# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from enum import IntEnum


class DFURequest(IntEnum):
    """
    DFU request.
    
    See ST Microelectronics application note AN3156.
    """
    
    DETACH = 0
    """
    Requests the device to leave DFU mode and enter the application.

    The Detach request is not meaningful in the case of the bootloader. The bootloader starts
    with a system reset depending on the boot mode configuration settings which means that
    no other application is running at that time.
    """

    DOWNLOAD = 1
    """
    Requests data transfer from Host to the device in order to load them
    into device internal flash memory. Includes also erase commands.
    """

    UPLOAD = 2
    """
    Requests data transfer from device to Host in order to load content
    of device internal flash memory into a Host file.
    """

    GET_STATUS = 3
    """
    Requests device to send status report to the Host (including status
    resulting from the last request execution and the state the device
    enters immediately after this request).
    """

    CLEAR_STATUS = 4
    """
    Requests device to clear error status and move to next step.
    """

    GET_STATE = 5
    """
    Requests the device to send only the state it enters immediately
    after this request.
    """

    ABORT = 6
    """
    Requests device to exit the current state/operation and enter idle
    state immediately
    """
