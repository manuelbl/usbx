# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import logging
import re
import time
from ctypes import byref, sizeof
from ctypes.wintypes import HANDLE, ULONG
from typing import Optional

from .deviceinfoset import DeviceInfoSet
from .kernel32 import kernel32, GENERIC_WRITE, GENERIC_READ, FILE_SHARE_WRITE, FILE_SHARE_READ, OPEN_EXISTING, \
    FILE_ATTRIBUTE_NORMAL, FILE_FLAG_OVERLAPPED
from .setupapi import DEVPKEY_Device_Children, DEVPKEY_Device_HardwareIds
from .winerror import raise_last_usb_error
from .winusb import winusb, WINUSB_INTERFACE_HANDLE, WINUSB_SETUP_PACKET, PUCHAR, PIPE_TRANSFER_TIMEOUT
from .._common.devicebase import DeviceBase
from ..configuration import Interface, Endpoint
from ..exceptions import USBError
from ..controltransfer import ControlTransfer
from ..enums import TransferDirection, Recipient
from .._common.ctypesfunc import readable_buffer, writable_buffer


class InterfaceHandle:
    def __init__(self, number: int, first_number: int):
        self.number: int = number
        self.first_number: int = first_number
        self.device_handle: Optional[HANDLE] = None
        self.winusb_handle: Optional[HANDLE] = None
        self.device_open_count: int = 0
        self.is_claimed: bool = False


def create_winusb_setup_packet(transfer: ControlTransfer, direction: TransferDirection) -> WINUSB_SETUP_PACKET:
    bm_request = ((0x80 if direction == TransferDirection.IN else 0x00) | (transfer.request_type.value << 5) |
                  transfer.recipient.value)
    return WINUSB_SETUP_PACKET(bm_request, transfer.request, transfer.value, transfer.index, 0)


class WindowsDevice(DeviceBase):
    def __init__(self, device_path: str, is_composite: bool, device_desc: bytes, config_desc: bytes):
        def handle_for_intf(intf: Interface) -> InterfaceHandle:
            first_intf_number = self.configuration.get_function(intf.number).first_intf_number
            return InterfaceHandle(intf.number, first_intf_number)

        super().__init__(device_path.casefold())
        self.is_composite: bool = is_composite
        self.set_descriptors(device_desc, config_desc)
        self.interface_handles: list[InterfaceHandle] = list(map(handle_for_intf, self.configuration.interfaces))
        self.device_paths: dict[int, str] = {}

    def open(self) -> None:
        with self._device_lock:
            self.check_is_closed_and_connected()
            self.is_open = True

    def close(self) -> None:
        with self._device_lock:
            self.is_open = False
            for intf in self.interface_handles:
                if intf.winusb_handle is not None:
                    winusb.WinUsb_Free(intf.winusb_handle)
                    intf.winusb_handle = None
                    intf.is_claimed = False
                    self.set_claimed(intf.number, False)
            for intf in self.interface_handles:
                if intf.device_handle is not None:
                    kernel32.CloseHandle(intf.device_handle)
                    intf.device_handle = None
                    intf.device_open_count = 0

    def claim_interface(self, number: int) -> None:
        # When a device is plugged in, a notification is sent. For composite devices, it is a notification
        # that the composite device is ready. Each composite function will be registered separately and
        # the related information will be available with a delay. So for composite functions, several
        # retries might be needed until the device path is available.
        num_retries = 30  # 30 x 100ms
        while True:
            if self.try_claim_interface(number):
                return  # success

            num_retries -= 1
            if num_retries == 0:
                raise USBError('claiming interface failed (function has no device path / interface GUID, '
                                   'might be missing WinUSB driver)')

            # sleep and retry
            logging.debug('Sleep for 100ms...')
            time.sleep(0.1)

    def try_claim_interface(self, number: int) -> bool:
        with self._device_lock:
            self.check_is_open()
            self.get_and_check_interface(number, False)
            intf_handle = self.get_interface_handle(number)
            if intf_handle.first_number == number:
                first_intf_handle = intf_handle
            else:
                first_intf_handle = self.get_interface_handle(intf_handle.first_number)

            # both the device and the first interface must be opened for any interface belonging to the same function
            if first_intf_handle.device_handle is None:
                device_path = self.get_interface_device_path(first_intf_handle.number)
                if device_path is None:
                    return False  # retry later

                logging.debug(f'opening device {device_path}')

                # open Windows device if needed
                device_handle = kernel32.CreateFileW(device_path, GENERIC_WRITE | GENERIC_READ,
                                                     FILE_SHARE_WRITE | FILE_SHARE_READ, None, OPEN_EXISTING,
                                                     FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED, None)
                if device_handle == -1:
                    raise_last_usb_error(f'claiming interface failed (opening USB device {device_path} failed)')

                try:
                    winusb_handle = WINUSB_INTERFACE_HANDLE()
                    if winusb.WinUsb_Initialize(device_handle, byref(winusb_handle)) == 0:
                        raise_last_usb_error('claiming interface failed')

                    first_intf_handle.device_handle = device_handle
                    first_intf_handle.winusb_handle = winusb_handle

                except:
                    kernel32.CloseHandle(device_handle)
                    raise

            if intf_handle != first_intf_handle:
                winusb_handle = WINUSB_INTERFACE_HANDLE()
                if winusb.WinUsb_GetAssociatedInterface(first_intf_handle.winusb_handle,
                                                        intf_handle.number - first_intf_handle.number - 1,
                                                        byref(winusb_handle)) == 0:
                    raise_last_usb_error('claiming (associated) interface failed')
                intf_handle.winusb_handle = winusb_handle

            first_intf_handle.device_open_count += 1
            intf_handle.is_claimed = True
            self.set_claimed(number, True)
            return True

    def release_interface(self, number: int) -> None:
        with self._device_lock:
            self.check_is_open()
            self.get_and_check_interface(number, True)

            intf_handle = self.get_interface_handle(number)
            if intf_handle.first_number == number:
                first_intf_handle = intf_handle
            else:
                first_intf_handle = self.get_interface_handle(intf_handle.first_number)

            if intf_handle != first_intf_handle:
                winusb.WinUsb_Free(intf_handle.winusb_handle)
                intf_handle.winusb_handle = None

            first_intf_handle.device_open_count -= 1
            if first_intf_handle.device_open_count == 0:
                winusb.WinUsb_Free(first_intf_handle.winusb_handle)
                first_intf_handle.winusb_handle = None

                logging.debug(f'closing device {self.get_cached_interface_device_path(number)}')

                kernel32.CloseHandle(first_intf_handle.device_handle)
                first_intf_handle.device_handle = None

            intf_handle.is_claimed = False
            self.set_claimed(number, False)

    def select_alternate(self, interface_number: int, alternate_number: int) -> None:
        with self._device_lock:
            self.check_alternate_interface(interface_number, alternate_number)

            handle = self.get_interface_handle(interface_number)
            if winusb.WinUsb_SetCurrentAlternateSetting(handle.winusb_handle, alternate_number) == 0:
                raise_last_usb_error(f'failed to set interface {interface_number} to alternate {alternate_number}')

            self.set_current_alternate(interface_number, alternate_number)

    def get_interface_device_path(self, number: int) -> Optional[str]:
        device_path = self.get_cached_interface_device_path(number)
        if device_path is not None:
            return device_path

        parent_device_path = self.identifier

        with DeviceInfoSet.of_path(parent_device_path) as device_info_set:
            children_instance_ids = device_info_set.get_string_list_property(DEVPKEY_Device_Children)
            if children_instance_ids is None:
                logging.debug(f'missing children instance IDs for device {parent_device_path}')
                return None

            logging.debug(f'children instance IDs: {children_instance_ids}')

            for instance_id in children_instance_ids:
                device_path = self.get_child_device_path(instance_id, number)
                if device_path is not None:
                    return device_path

        return None

    def get_child_device_path(self, instance_id: str, number: int) -> Optional[str]:
        with DeviceInfoSet.of_instance(instance_id) as device_info_set:
            # get hardware IDs (to extract interface number)
            hardware_ids = device_info_set.get_string_list_property(DEVPKEY_Device_HardwareIds)
            if hardware_ids is None:
                logging.debug(f'child device {instance_id} has no hardware IDs')
                return None

            intf_number = self.extract_interface_number(hardware_ids)
            if intf_number is None:
                logging.debug(f'child device {instance_id} has no interface number')
                return None

            if intf_number != number:
                return None

            device_path = device_info_set.get_device_path_by_guid(instance_id)
            if device_path is None:
                logging.info(f'Child device {instance_id} has no device path / interface GUID')
                raise USBError('claiming interface failed (function has no device path / interface GUID, '
                                   'might be missing WinUSB driver)')

            self.device_paths[number] = device_path
            return device_path

    MULTIPLE_INTERFACE_ID = re.compile(r'USB\\VID_[0-9A-Fa-f]{4}&PID_[0-9A-Fa-f]{4}&MI_([0-9A-Fa-f]{2})')

    def extract_interface_number(self, hardware_ids: list[str]) -> Optional[int]:
        for hardware_id in hardware_ids:
            match = self.MULTIPLE_INTERFACE_ID.match(hardware_id)
            if match is not None:
                try:
                    return int(match.group(1))
                except ValueError:
                    # ignore
                    pass
        return None

    def get_cached_interface_device_path(self, number: int) -> Optional[str]:
        if not self.is_composite:
            return self.identifier
        return self.device_paths.get(number)

    def get_interface_handle(self, number: int) -> InterfaceHandle:
        handle = next((handle for handle in self.interface_handles if handle.number == number), None)
        if handle is None:
            raise USBError(f'device has no interface {number}')
        return handle

    def control_transfer_in(self, transfer: ControlTransfer, length: int) -> bytes:
        with self._device_lock:
            self.check_control_transfer(transfer, TransferDirection.IN)
            handle = self.get_winusb_handle(transfer.recipient, transfer.index)

        setup_packet = create_winusb_setup_packet(transfer, TransferDirection.IN)
        buffer = bytearray(length)
        length_transferred = ULONG()
        if winusb.WinUsb_ControlTransfer(
                handle,
                setup_packet,
                writable_buffer(buffer, PUCHAR),
                length,
                byref(length_transferred),
                None
        ) == 0:
            raise_last_usb_error('control transfer IN failed')
        return bytes(buffer[:length_transferred.value])

    def control_transfer_out(self, transfer: ControlTransfer, data: bytes = None) -> None:
        with self._device_lock:
            self.check_control_transfer(transfer, TransferDirection.OUT)
            handle = self.get_winusb_handle(transfer.recipient, transfer.index)

        setup_packet = create_winusb_setup_packet(transfer, TransferDirection.OUT)
        length = len(data) if data is not None else 0
        buffer = readable_buffer(data, PUCHAR) if data is not None else None
        length_transferred = ULONG()
        if winusb.WinUsb_ControlTransfer(
                handle,
                setup_packet,
                buffer,
                length,
                byref(length_transferred),
                None
        ) == 0:
            raise_last_usb_error('control transfer OUT failed')

    def transfer_in(self, endpoint_number: int, timeout: Optional[float] = None) -> bytes:
        with self._device_lock:
            endpoint, interface = self.get_and_check_endpoint_and_interface(endpoint_number, TransferDirection.IN)
            handle = self.get_interface_handle(interface.number).winusb_handle

        address = Endpoint.get_address(endpoint_number, TransferDirection.IN)
        timeout_value = ULONG(int(timeout * 1000 + 0.5) if timeout is not None else 0)
        if winusb.WinUsb_SetPipePolicy(handle, address, PIPE_TRANSFER_TIMEOUT, sizeof(timeout_value),
                                       byref(timeout_value)) == 0:
            raise_last_usb_error(f'internal error: unable to set pipe policy for IN endpoint {endpoint_number}')

        buffer = bytearray(endpoint.max_packet_size)
        transferred = ULONG()
        if winusb.WinUsb_ReadPipe(handle, address, writable_buffer(buffer, PUCHAR),
                                  endpoint.max_packet_size, byref(transferred), None) == 0:
            raise_last_usb_error(f'transfer IN from endpoint {endpoint_number} failed')
        return bytes(buffer[:transferred.value])

    def transfer_out(self, endpoint_number: int, data: bytes, timeout: Optional[float] = None) -> None:
        with self._device_lock:
            _, interface = self.get_and_check_endpoint_and_interface(endpoint_number, TransferDirection.OUT)
            handle = self.get_interface_handle(interface.number).winusb_handle

        address = Endpoint.get_address(endpoint_number, TransferDirection.OUT)
        timeout_value = ULONG(int(timeout * 1000 + 0.5) if timeout is not None else 0)
        if winusb.WinUsb_SetPipePolicy(handle, address, PIPE_TRANSFER_TIMEOUT, sizeof(timeout_value),
                                       byref(timeout_value)) == 0:
            raise_last_usb_error(f'internal error: unable to set pipe policy for OUT endpoint {endpoint_number}')

        transferred = ULONG()
        if winusb.WinUsb_WritePipe(handle, address, readable_buffer(data, PUCHAR), len(data),
                                   byref(transferred), None) == 0:
            raise_last_usb_error(f'transfer OUT to endpoint {endpoint_number} failed')

    def clear_halt(self, number: int, direction: TransferDirection) -> None:
        with self._device_lock:
            _, interface = self.get_and_check_endpoint_and_interface(number, direction)
            handle = self.get_interface_handle(interface.number).winusb_handle

        address = Endpoint.get_address(number, direction)
        if winusb.WinUsb_ResetPipe(handle, address) == 0:
            raise_last_usb_error(f'internal error: unable to clear halt of endpoint {number} {direction.name}')

    def abort_transfers(self, number: int, direction: TransferDirection) -> None:
        with self._device_lock:
            _, interface = self.get_and_check_endpoint_and_interface(number, direction)
            handle = self.get_interface_handle(interface.number).winusb_handle

        address = Endpoint.get_address(number, direction)
        if winusb.WinUsb_AbortPipe(handle, address) == 0:
            raise_last_usb_error(f'internal error: unable to abort transfer from/to endpoint {number} {direction.name}')


    def get_winusb_handle(self, recipient: Recipient, index: int) -> WINUSB_INTERFACE_HANDLE:
        if recipient == Recipient.INTERFACE:
            return self.get_interface_handle(index & 0xff).winusb_handle

        if recipient == Recipient.ENDPOINT:
            address = index & 0xff
            _, intf = self.get_endpoint_and_interface(Endpoint.get_number(address), Endpoint.get_direction(address))
            return self.get_interface_handle(intf.number).winusb_handle

        # for control transfer to device, use any claimed interface
        for intf_handle in self.interface_handles:
            if intf_handle.winusb_handle is not None:
                return intf_handle.winusb_handle

        raise USBError('control transfer to device not possible as not interface has been claimed')
