# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from __future__ import annotations

import time
from ctypes import POINTER, byref, c_uint8, cast, c_uint16, c_uint32
from typing import Union, Optional

from .macoserrors import check_result
from .iokit import io_object_t, iokit, IOUSBFindInterfaceRequest, get_plugin_interface, \
    kIOUSBInterfaceUserClientTypeID, kIOUSBInterfaceInterfaceID190, IOUSBInterfaceInterface190, IOUSBDevRequest, \
    USBConfigurationDescriptor, IOUSBInterfaceHandle, kIOUSBFindInterfaceDontCare, kIOReturnAborted, \
    guard_iokit_object, IOKitGuard, kIOReturnExclusiveAccess, kUSBReEnumerateCaptureDeviceMask, \
    kUSBReEnumerateReleaseDeviceMask
from .transfertimeout import TransferTimeout
from .._common.confparser import device_descriptor_type
from .._common.ctypesfunc import readable_buffer, writable_buffer
from .._common.devicebase import DeviceBase
from ..configuration import Interface, Endpoint
from ..controltransfer import ControlTransfer
from ..enums import RequestType, Recipient
from ..enums import TransferType, TransferDirection
from ..exceptions import TransferTimeoutError


def transfer_type_from_macos(macos_transfer_type: int) -> TransferType:
    if macos_transfer_type == 1:
        return TransferType.ISOCHRONOUS
    elif macos_transfer_type == 2:
        return TransferType.BULK
    elif macos_transfer_type == 3:
        return TransferType.INTERRUPT
    else:
        return TransferType.CONTROL


def create_device_request(direction: TransferDirection, setup: ControlTransfer,
                          data: Optional[Union[bytes, bytearray]]) -> IOUSBDevRequest:
    request = IOUSBDevRequest()
    request.bmRequestType = (0x80 if direction == TransferDirection.IN else 0x00) | (
                setup.request_type << 5) | setup.recipient
    request.bRequest = setup.request
    request.wValue = setup.value
    request.wIndex = setup.index
    request.wLength = len(data) if data is not None else 0
    if request.wLength != 0:
        if direction == TransferDirection.IN:
            request.pData = writable_buffer(data)
        else:
            request.pData = readable_buffer(data)
    return request


class USBInterfaceInfo:
    def __init__(self, iokit_intf: IOUSBInterfaceHandle, desc: Interface):
        self.iokit_intf: IOUSBInterfaceHandle = iokit_intf
        self.desc: Interface = desc


class USBEndpointInfo:
    def __init__(self, iokit_intf: IOUSBInterfaceHandle, pipe_index: int,
                 transfer_type: TransferType, packet_size: int):
        self.iokit_intf: IOUSBInterfaceHandle = iokit_intf
        self.pipe_index: int = pipe_index
        self.transfer_type: TransferType = transfer_type
        self.packet_size: int = packet_size


class MacosDevice(DeviceBase):

    def __init__(self, device_intf: IOUSBInterfaceHandle, identifier: str):
        super().__init__(identifier)
        self.discovery_time = time.time()

        self.device_intf: IOUSBInterfaceHandle = device_intf

        device_desc = self.load_device_desc()
        config_desc = self.load_configuration()
        self.set_descriptors(device_desc, config_desc)

        self.claimed_interfaces: list[USBInterfaceInfo] = []
        self.endpoints: dict[int, USBEndpointInfo] = {}

        self.device_intf.contents.contents.AddRef(self.device_intf)

    def __del__(self):
        with self._device_lock:
            self.device_intf.contents.contents.Release(self.device_intf)

    def load_configuration(self) -> bytes:
        config_desc = POINTER(USBConfigurationDescriptor)()
        self.device_intf.contents.contents.GetConfigurationDescriptorPtr(self.device_intf, 0, byref(config_desc))
        total_length = config_desc.contents.wTotalLength
        config_desc_array = cast(config_desc, POINTER(c_uint8 * total_length)).contents
        return bytes(config_desc_array)

    def load_device_desc(self) -> bytes:
        buffer = bytearray(255)
        request = create_device_request(
            TransferDirection.IN,
            ControlTransfer(
                RequestType.STANDARD,
                Recipient.DEVICE,
                6,  # get descriptor
                device_descriptor_type << 8,
                0
            ),
            buffer
        )

        result = self.device_intf.contents.contents.DeviceRequest(self.device_intf, byref(request))
        check_result(result, 'Failed to load device descriptor')

        return bytes(buffer[:request.wLenDone])

    def open(self) -> None:
        with self._device_lock:
            self.check_is_closed_and_connected()

            # several retries if device has just been connected/discovered
            duration = time.time() - self.discovery_time
            num_tries = int(max((1 - duration) / 0.09, 1))

            result = 0
            while num_tries > 0:
                num_tries -= 1
                result = self.device_intf.contents.contents.USBDeviceOpenSeize(self.device_intf)
                if result != kIOReturnExclusiveAccess:
                    break
                time.sleep(0.09)

            check_result(result, 'Unable to open device')

            self.is_open = True
            self.claimed_interfaces = []
            self.endpoints = {}

            result = self.device_intf.contents.contents.SetConfiguration(self.device_intf, self.configuration_value)
            check_result(result, 'Unable to set device configuration')

    def close(self) -> None:
        with self._device_lock:
            if not self.is_open:
                return

            self.release_all_interfaces()
            self.is_open = False
            self.device_intf.contents.contents.USBDeviceClose(self.device_intf)

    def claim_interface(self, number: int) -> None:
        with self._device_lock:
            self.check_is_open()
            desc = self.get_and_check_interface(number, False)

            info = self.find_interface_info(desc)
            try:
                result = info.iokit_intf.contents.contents.USBInterfaceOpenSeize(info.iokit_intf)
                check_result(result, 'Failed to claim interface')

                info.iokit_intf.contents.contents.AddRef(info.iokit_intf)
                self.claimed_interfaces.append(info)
                self.set_claimed(number, True)
                self.update_endpoint_info()

            finally:
                info.iokit_intf.contents.contents.Release(info.iokit_intf)

    def release_interface(self, number: int) -> None:
        with self._device_lock:
            self.check_is_open()
            self.get_and_check_interface(number, True)
            info = next((i for i in self.claimed_interfaces if i.desc.number == number), None)

            result = info.iokit_intf.contents.contents.USBInterfaceClose(info.iokit_intf)
            check_result(result, 'Failed to release interface')

            self.claimed_interfaces.remove(info)
            self.set_claimed(number, False)

            info.iokit_intf.contents.contents.Release(info.iokit_intf)
            self.update_endpoint_info()

    def release_all_interfaces(self) -> None:
        for intf_info in self.claimed_interfaces:
            intf_info.iokit_intf.contents.contents.USBInterfaceClose(intf_info.iokit_intf)  # best effort; ignore errors
            intf_info.iokit_intf.contents.contents.Release(intf_info.iokit_intf)
            self.set_claimed(intf_info.desc.number, False)

        self.claimed_interfaces = []
        self.endpoints = {}

    def select_alternate(self, interface_number: int, alternate_number: int) -> None:
        with self._device_lock:
            self.check_alternate_interface(interface_number, alternate_number)
            info = next((i for i in self.claimed_interfaces if i.desc.number == interface_number), None)

            result = info.iokit_intf.contents.contents.SetAlternateInterface(info.iokit_intf, alternate_number)
            check_result(result, 'Failed to set alternate interface')

            self.set_current_alternate(interface_number, alternate_number)
            self.update_endpoint_info()

    def control_transfer_in(self, transfer: ControlTransfer, length: int) -> bytes:
        with guard_iokit_object() as guard:
            with self._device_lock:
                self.check_control_transfer(transfer, TransferDirection.IN)
                guard.retain(self.device_intf)

            buffer = bytearray(length)
            request = create_device_request(TransferDirection.IN, transfer, buffer)
            result = self.device_intf.contents.contents.DeviceRequest(self.device_intf, byref(request))
            check_result(result, 'Control transfer IN failed')

            return bytes(buffer[:request.wLenDone])

    def control_transfer_out(self, transfer: ControlTransfer, data: bytes = None) -> None:
        with guard_iokit_object() as guard:
            with self._device_lock:
                self.check_control_transfer(transfer, TransferDirection.OUT)
                guard.retain(self.device_intf)

            request = create_device_request(TransferDirection.OUT, transfer, data)
            result = self.device_intf.contents.contents.DeviceRequest(self.device_intf, byref(request))
            check_result(result, 'Control transfer OUT failed')

    def transfer_in(self, endpoint_number: int, timeout: Optional[float] = None) -> bytes:
        with guard_iokit_object() as guard:
            iokit_intf, pipe_index, endpoint = self.get_retained_handle(endpoint_number, TransferDirection.IN, guard)

            buffer = bytearray(endpoint.max_packet_size)
            size = c_uint32(len(buffer))
            if timeout is None:
                result = iokit_intf.contents.contents.ReadPipe(iokit_intf, pipe_index, writable_buffer(buffer), byref(size))
            elif endpoint.transfer_type == TransferType.BULK:
                timeout_ms = int(timeout * 1000 + 0.5)
                result = iokit_intf.contents.contents.ReadPipeTO(iokit_intf, pipe_index, writable_buffer(buffer),
                                                                 byref(size), timeout_ms, timeout_ms)
            else:
                timeout_ms = int(timeout * 1000 + 0.5)
                transfer_timeout = TransferTimeout(timeout_ms, iokit_intf, pipe_index)
                result = iokit_intf.contents.contents.ReadPipe(iokit_intf, pipe_index, writable_buffer(buffer), byref(size))
                if result == kIOReturnAborted:
                    raise TransferTimeoutError('transfer timed out')
                transfer_timeout.cancel()
            check_result(result, f'Transfer IN from endpoint {endpoint_number} failed')
            return bytes(buffer[:size.value])

    def transfer_out(self, endpoint_number: int, data: bytes, timeout: Optional[float] = None) -> None:
        with guard_iokit_object() as guard:
            iokit_intf, pipe_index, endpoint = self.get_retained_handle(endpoint_number, TransferDirection.OUT, guard)

            if timeout is None:
                result = iokit_intf.contents.contents.WritePipe(iokit_intf, pipe_index, readable_buffer(data), len(data))
            elif endpoint.transfer_type == TransferType.BULK:
                timeout_ms = int(timeout * 1000 + 0.5)
                result = iokit_intf.contents.contents.WritePipeTO(iokit_intf, pipe_index, readable_buffer(data), len(data),
                                                                  timeout_ms, timeout_ms)
            else:
                timeout_ms = int(timeout * 1000 + 0.5)
                transfer_timeout = TransferTimeout(timeout_ms, iokit_intf, pipe_index)
                result = iokit_intf.contents.contents.WritePipe(iokit_intf, pipe_index, readable_buffer(data), len(data))
                if result == kIOReturnAborted:
                    raise TransferTimeoutError('transfer timed out')
                transfer_timeout.cancel()
            check_result(result, f'Transfer OUT to endpoint {endpoint_number} failed')

    def clear_halt(self, number: int, direction: TransferDirection) -> None:
        with guard_iokit_object() as guard:
            iokit_intf, pipe_index, _ = self.get_retained_handle(number, direction, guard)
            result = iokit_intf.contents.contents.ClearPipeStallBothEnds(iokit_intf, pipe_index)
            check_result(result, 'Clearing halt condition failed')

    def abort_transfers(self, number: int, direction: TransferDirection) -> None:
        with guard_iokit_object() as guard:
            iokit_intf, pipe_index, _ = self.get_retained_handle(number, direction, guard)
            result = iokit_intf.contents.contents.AbortPipe(iokit_intf, pipe_index)
            check_result(result, 'Aborting endpoint transfers failed')

    def get_retained_handle(self, endpoint_number: int, direction: TransferDirection, guard: IOKitGuard) -> (IOUSBInterfaceHandle, int, Endpoint):
        with self._device_lock:
            endpoint, interface = self.get_and_check_endpoint_and_interface(endpoint_number, direction)
            address = Endpoint.get_address(endpoint_number, direction)
            pipe_index = self.endpoints[address].pipe_index
            iokit_intf = self.find_intf_handle(interface)
            guard.retain(iokit_intf)
            return iokit_intf, pipe_index, endpoint

    def find_intf_handle(self, interface: Interface) -> IOUSBInterfaceHandle:
        return next(intf.iokit_intf for intf in self.claimed_interfaces if intf.desc == interface)

    def find_interface_info(self, desc: Interface) -> USBInterfaceInfo:
        """
        Iterates the list of interfaces to get the handle for the IOKit Interface.
        :param desc: interface descriptor
        :return: :class:`InterfaceInfo` instance consisting of handle and descriptor
        """
        request = IOUSBFindInterfaceRequest(kIOUSBFindInterfaceDontCare, kIOUSBFindInterfaceDontCare,
                                            kIOUSBFindInterfaceDontCare, kIOUSBFindInterfaceDontCare)
        iterator = io_object_t()
        result = self.device_intf.contents.contents.CreateInterfaceIterator(self.device_intf, byref(request),
                                                                            byref(iterator))
        check_result(result, 'Internal error (enumerating interfaces)')

        while True:
            service: io_object_t = iokit.IOIteratorNext(iterator)
            intf: IOUSBInterfaceHandle = None
            if service == 0:
                break

            try:
                intf = get_plugin_interface(service, kIOUSBInterfaceUserClientTypeID, kIOUSBInterfaceInterfaceID190,
                                            IOUSBInterfaceInterface190)
                if intf is None:
                    continue

                intf_num = c_uint8()
                intf.contents.contents.GetInterfaceNumber(intf, byref(intf_num))
                if intf_num.value != desc.number:
                    continue

                intf.contents.contents.AddRef(intf)
                return USBInterfaceInfo(intf, desc)

            finally:
                if intf is not None:
                    intf.contents.contents.Release(intf)

                result = iokit.IOObjectRelease(service)
                check_result(result, 'Internal error (getting interface info)')

    def update_endpoint_info(self) -> None:
        num_endpoints = c_uint8()
        direction = c_uint8()
        number = c_uint8()
        transfer_type = c_uint8()
        max_packet_size = c_uint16()
        interval = c_uint8()
        endpoints: dict[int, USBEndpointInfo] = {}

        for intf_info in self.claimed_interfaces:
            intf = intf_info.iokit_intf
            result = intf.contents.contents.GetNumEndpoints(intf, byref(num_endpoints))
            check_result(result, 'Internal error (getting number of endpoints)')

            for pipe_index in range(1, num_endpoints.value + 1):
                result = intf.contents.contents.GetPipeProperties(intf, pipe_index, byref(direction), byref(number),
                                                                  byref(transfer_type), byref(max_packet_size),
                                                                  byref(interval))
                check_result(result, 'Internal error (getting endpoint info)')

                address = (direction.value << 7) | number.value
                endpoints[address] = USBEndpointInfo(intf, pipe_index, transfer_type_from_macos(transfer_type.value),
                                                     max_packet_size.value)
        self.endpoints = endpoints

    def detach_standard_drivers(self) -> None:
        with self._device_lock:
            self.check_is_closed_and_connected()
            result = self.device_intf.contents.contents.USBDeviceReEnumerate(self.device_intf,
                                                                             kUSBReEnumerateCaptureDeviceMask)
            check_result(result, 'Detaching standard drivers failed')

    def attach_standard_drivers(self) -> None:
        with self._device_lock:
            self.check_is_closed_and_connected()
            result = self.device_intf.contents.contents.USBDeviceReEnumerate(self.device_intf,
                                                                             kUSBReEnumerateReleaseDeviceMask)
            check_result(result, 'Attaching standard drivers failed')
