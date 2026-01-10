# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import struct
import time
from typing import Optional

from devicestate import DeviceState
from devicestatus import DeviceStatus
from dfuerror import DFUError
from dfurequest import DFURequest
from dfustatus import DFUStatus
from segment import Page, Segment
from usbx import ControlTransfer, Device, Recipient, RequestType, Version, usb


class DFUDevice:
    """
    DFU device.
    
    Implements the DFU operations like download, upload etc.
    """

    FLASH_BASE_ADDRESS: int = 0x08000000

    @staticmethod
    def find_devices() -> list['DFUDevice']:
        """
        Gets all connected DFU devices
        """
        return list(map(DFUDevice, usb.find_devices(DFUDevice.has_dfu_descriptor)))
    
    @staticmethod
    def has_dfu_descriptor(device: Device) -> bool:
        """
        Checks if the device has a DFU functional descriptor.
        """
        return DFUDevice.get_dfu_descriptor_offset(device.configuration_descriptor) > 0 and DFUDevice.get_dfu_interface_number(device) >= 0
    
    @staticmethod
    def get_dfu_descriptor_offset(descriptor: bytes) -> int:
        """
        Gets the offset of the DFU functional descriptor within the USB configuration descriptor.
        """
        offset = 0
        while offset < len(descriptor):
            if descriptor[offset + 1] == 0x21:
                return offset
            offset += descriptor[offset]
        return -1
    
    @staticmethod
    def get_dfu_interface_number(device: Device) -> int:
        """
        Gets the DFU interface number
        """
        for intf in device.configuration.interfaces:
            alternate = intf.current_alternate
            if alternate.class_code == 0xfe and alternate.subclass_code == 0x01 and alternate.protocol_code == 0x02:
                return intf.number
        return -1
    
    def __init__(self, device: Device):
        """
        Creates a new DFUDevice instance.

        The specified USB device must have a DFU descriptor and a DFU interface.
        """
        self.device: Device = device
        self.interface_number: int = DFUDevice.get_dfu_interface_number(device)
        """Interface number"""

        descriptor = device.configuration_descriptor
        offset = DFUDevice.get_dfu_descriptor_offset(descriptor)

        self.detach_timeout: float = struct.unpack_from('<h', descriptor, offset=offset+3)[0] / 1000
        """
        Time, in seconds, that the device waits after receipt of the DFU_DETACH request. If this time
        elapses without a USB reset, then the device terminates the Reconfiguration phase and reverts to
        normal operation. This represents the maximum time that the device can wait (depending on its timers,
        etc.). The host may specify a shorter timeout in the DFU_DETACH request.
        """

        self.transfer_size: int = struct.unpack_from('<h', descriptor, offset=offset+5)[0]
        """
        Maximum number of bytes that the device can accept per control-write transaction: wTransferSize depends
        on the firmware implementation on each MCU.
        """

        self.dfu_version: Version = Version(struct.unpack_from('<h', descriptor, offset=offset+7)[0])
        """DFU protocol version"""

        self.segments: list[Segment] = []
        """List of segments (available after opening the device)"""

        self.attributes = descriptor[offset+2]
        """DFU attributes"""

    @property
    def serial_number(self) -> str:
        """
        Device serial number
        """
        return self.device.serial
    
    @property
    def can_download(self) -> bool:
        return (self.attributes & 1) != 0

    @property
    def can_upload(self) -> bool:
        return (self.attributes & 2) != 0

    @property
    def is_manifestation_toleration(self) -> bool:
        """
        Device is able to communicate via USB after Manifestation phase 
        """
        return (self.attributes & 4) != 0

    @property
    def will_detach(self) -> bool:
        """
        Device will perform a bus detach-attach sequence when it receives a
        DFU_DETACH request.
        """
        return (self.attributes & 8) != 0

    def open(self) -> None:
        """
        Opens the DFU device for communication
        """
        self.device.open()
        self.device.claim_interface(self.interface_number)
        self.segments = Segment.get_segments(self.device, self.interface_number)
        self.clear_error_if_needed()

    def close(self) -> None:
        """
        Closes the DFU device.
        """
        self.device.close()

    def get_status(self) -> DFUStatus:
        """
        Gets the full device status.
        """
        transfer = self.create_dfu_control_transfer(DFURequest.GET_STATUS)
        status_bytes = self.device.control_transfer_in(transfer, 6)
        if len(status_bytes) != 6:
            raise DFUError("Invalid response for GET_STATUS request")
        return DFUStatus.from_bytes(status_bytes)
    
    def clear_status(self) -> None:
        """
        Clears an error status.
        """
        transfer = self.create_dfu_control_transfer(DFURequest.CLEAR_STATUS)
        self.device.control_transfer_out(transfer)

    def clear_error_if_needed(self) -> None:
        status = self.get_status()
        if status.status != DeviceStatus.OK:
            self.clear_status()
            time.sleep(status.poll_timeout)
            status = self.get_status()
            if status.status != DeviceStatus.OK:
                raise DFUError("Unable to clear error status")

    def abort(self) -> None:
        """
        Aborts download mode.
        """
        transfer = self.create_dfu_control_transfer(DFURequest.ABORT)
        self.device.control_transfer_out(transfer)

    def read(self, address: int, length: int) -> bytes:
        """
        Reads from the device flash memory.
        """

        self.expect_state(DeviceState.DFU_IDLE, DeviceState.DFU_DNLOAD_IDLE)
        self.set_address(address)
        self.exit_mode()
        self.expect_state(DeviceState.DFU_IDLE, DeviceState.DFU_UPLOAD_IDLE)

        result = bytearray()

        ## read full chunks
        offset = 0
        block_num = 2
        while offset < length:
            chunk_size = min(self.transfer_size, length - offset)
            transfer = self.create_dfu_control_transfer(DFURequest.UPLOAD, block_num)
            chunk = self.device.control_transfer_in(transfer, chunk_size)
            result += chunk
            offset += chunk_size
            block_num += 1

        self.exit_mode()
        
        return result
    
    def verify(self, firmware: bytes) -> None:
        """
        Verifies that the device firmware is equal to the provided firmware
        (assuming base address 0x08000000)
        """
        firmware2 = self.read(DFUDevice.FLASH_BASE_ADDRESS, len(firmware))
        if firmware != firmware2:
            raise DFUError("Verification failed - content differs")
    
    def download(self, firmware: bytes) -> None:
        """
        Writes the provided firmware to the devices (at the STM32 base address of 0x08000000)
        """
        length = len(firmware)

        # validate start and end address exist and are writable
        start_address = DFUDevice.FLASH_BASE_ADDRESS
        first_page = self.get_writable_page(start_address)
        self.get_writable_page(start_address + length)

        self.device.select_alternate(self.interface_number, first_page.segment.alt_setting)
        print(f"Target memory segment: {first_page.segment.name}")

        # erase if needed
        if first_page.is_erasable:
            self.erase(start_address, length)

        # download firmware
        self.set_address(start_address)

        offset = 0
        transaction = 2
        while offset < length:
            chunk_size = min(length - offset, self.transfer_size)
            chunk = firmware[offset:offset+chunk_size]

            print(f"Writing data at 0x{(start_address + offset):08x} (size 0x{chunk_size:x})")
            transfer = self.create_dfu_control_transfer(DFURequest.DOWNLOAD, transaction)
            self.device.control_transfer_out(transfer, chunk)

            self.finish_download_command("writing data")

            offset += chunk_size
            transaction += 1

        self.exit_mode()

    def erase(self, start_address: int, length: int) -> None:
        """
        Erases the specified range.

        Only applicable to erasable sectors, i.e. flash memory.

        Only entire pages can be erased. If start and end address do not fall onto
        page boundaries, this method will extend the range to be erased.
        """
        
        end_address = start_address + length

        while start_address < end_address:
            page = self.find_page(start_address)
            if page is None:
                raise DFUError(f"No valid memory segment at address 0x{start_address:0x8}")
            if not page.is_erasable:
                raise DFUError(f"Page at address 0x{start_address:0x8} is not erasable")

            print(f"Erasing page at 0x{start_address:08x} (size 0x{page.page_size:x})")
            self.erase_page(page.start_address)
            start_address = page.end_address

    def wait_for_disconnect(self) -> None:
        """
        Waits until the device disconnects.
        
        Disconnection is a side effect of leaving DFU mode.

        If the device does not disconnect after 5 seconds,
        an exception will be thrown.
        """
        waiting_time = 5
        while waiting_time > 0 and self.device.is_connected:
            time.sleep(0.1)
            waiting_time -= 0.1

        if self.device.is_connected:
            raise DFUError("Device did not restart (try disconnecting and reconnecting it)")

    def erase_page(self, address: int) -> None:
        self.exec_special_command(0x41, "erasing page", address)

    def get_writable_page(self, address: int) -> Page:
        page = self.find_page(address)
        if page is None:
            raise DFUError(f"No valid memory segment at address 0x{address:08x}")
        if not page.is_writable:
            raise DFUError(f"Page at address 0x{address:08x} is not writable")
        return page
    
    def find_page(self, address: int) -> Optional[Page]:
        return Segment.find_page(self.segments, address)

    def set_address(self, address: int) -> None:
        self.exec_special_command(0x21, "setting address", address)

    def exec_special_command(self, command_byte: int, action: str, address: int) -> None:
        transfer = self.create_dfu_control_transfer(DFURequest.DOWNLOAD)
        data = bytes([command_byte]) + struct.pack('<I', address)
        self.device.control_transfer_out(transfer, data)
        self.finish_download_command(action)

    def finish_download_command(self, action: str) -> None:
        status = self.get_status()
        if status.state != DeviceState.DFU_DNBUSY:
            raise DFUError(f"Unexpected state for {action}")
        
        time.sleep(status.poll_timeout)

        status = self.get_status()
        if status.status != DeviceStatus.OK:
            raise DFUError(f"Unexpected status after {action}")
        
        time.sleep(status.poll_timeout)

    def exit_mode(self) -> None:
        self.abort()

        status = self.get_status()
        if status.state != DeviceState.DFU_IDLE:
            raise DFUError("Unexpected state after exiting from download mode")
        
        time.sleep(status.poll_timeout)

    def start_application(self) -> None:
        self.expect_state(DeviceState.DFU_IDLE, DeviceState.DFU_DNLOAD_IDLE)

        # By sending a zero-length download packet and querying the status,
        # the device will leave DFU mode and restart.
        transfer = self.create_dfu_control_transfer(DFURequest.DOWNLOAD)
        self.device.control_transfer_out(transfer)

        status = self.get_status()
        if status.state != DeviceState.DFU_MANIFEST:
            raise DFUError("Exiting DFU mode and starting firmware has failed")

    def expect_state(self, state1: DeviceState, state2: DeviceState) -> None:
        status = self.get_status()
        if status.state != state1 and status.state != state2:
            raise DFUError(f"Expected state {state1} or {state2} but got {status.state}")
        
    def create_dfu_control_transfer(self, request: DFURequest, value: int = 0) -> ControlTransfer:
        return ControlTransfer(RequestType.CLASS, Recipient.INTERFACE, request, value, self.interface_number)
