# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import logging
import struct
from ctypes import byref, sizeof, resize, cast, wstring_at
from ctypes.wintypes import HANDLE, DWORD, ULONG, HWND, UINT, WPARAM, LPARAM, MSG, LPCWSTR
from typing import Optional

from .deviceinfoset import DeviceInfoSet
from .kernel32 import kernel32, GENERIC_WRITE, FILE_SHARE_WRITE, OPEN_EXISTING
from .setupapi import GUID_DEVINTERFACE_USB_DEVICE, DEVPKEY_Device_InstanceId, DEVPKEY_Device_Address, \
    DEVPKEY_Device_Parent, GUID_DEVINTERFACE_USB_HUB
from .user32 import user32, WNDCLASSEXW, DEV_BROADCAST_DEVICEINTERFACE_W, WNDPROC, HWND_MESSAGE, \
    DEVICE_NOTIFY_WINDOW_HANDLE, DBT_DEVTYP_DEVICEINTERFACE, WM_DEVICECHANGE, DBT_DEVICEREMOVECOMPLETE, \
    DBT_DEVICEARRIVAL
from .windevice import WindowsDevice
from .winerror import raise_last_error
from .winusb import USB_NODE_CONNECTION_INFORMATION_EX, IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX, SetupPacket, \
    USB_DESCRIPTOR_REQUEST, IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION
from .._common.registrybase import DeviceRegistryBase
from ..device import Device
from ..exceptions import USBError


class WindowsDeviceRegistry(DeviceRegistryBase):
    def monitor_devices(self) -> None:
        instance = kernel32.GetModuleHandleW(None)

        # register window class
        wx = WNDCLASSEXW()
        wx.lpfnWndProc = WNDPROC(self.handle_windows_message)
        wx.hInstance = instance
        wx.lpszClassName = 'USB_MONITOR'
        atom = user32.RegisterClassExW(byref(wx))
        if atom == 0:
            raise_last_error('internal error (RegisterClassExW)')

        # create message-only window
        hwnd = user32.CreateWindowExW(0, 'USB_MONITOR', 'USB device monitor', 0, 0, 0, 0, 0, HWND_MESSAGE, None,
                                      instance, None)
        if hwnd == 0:
            raise_last_error('internal error (CreateWindowExW)')

        # configure notifications
        notification_filter = DEV_BROADCAST_DEVICEINTERFACE_W()
        notification_filter.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        notification_filter.dbcc_classguid = GUID_DEVINTERFACE_USB_DEVICE
        notify_handle = user32.RegisterDeviceNotificationW(hwnd, byref(notification_filter),
                                                           DEVICE_NOTIFY_WINDOW_HANDLE)
        if notify_handle == 0:
            raise_last_error('internal error (RegisterDeviceNotificationW)')

        try:
            self.notify_enumeration_complete(self.enumerate_present_devices())
        except Exception as exception:
            self.notify_enumeration_failed(exception)
            return

        msg = MSG()
        while True:
            err = user32.GetMessageW(msg, hwnd, 0, 0)
            if err <= 0:
                break

        if err == -1:
            raise_last_error('internal error (GetMessageW)')

    def handle_windows_message(self, hwnd: HWND, umsg: UINT, wparam: WPARAM, lparam: LPARAM) -> int:
        # check for message related to connecting / disconnecting devices
        if umsg == WM_DEVICECHANGE and (wparam == DBT_DEVICEARRIVAL or wparam == DBT_DEVICEREMOVECOMPLETE):
            device_path = wstring_at(cast(lparam + DEV_BROADCAST_DEVICEINTERFACE_W.dbcc_name.offset, LPCWSTR))
            if wparam == DBT_DEVICEARRIVAL:
                self.on_device_connected(device_path)
            else:
                self.on_device_disconnected(device_path)
            return 0

        return user32.DefWindowProcW(hwnd, umsg, wparam, lparam)

    def on_device_connected(self, device_path: str) -> None:
        device_info_set = DeviceInfoSet.of_path(device_path)
        hub_handles: dict[str, HANDLE] = {}
        try:
            device = self.create_device_from_device_info(device_info_set, device_path, hub_handles)
            self.add_device(device)
        except Exception as ex:
            logging.warning(f'failed to retrieve information about device {device_path} - ignoring device', exc_info=ex)
        finally:
            for handle in hub_handles.values():
                kernel32.CloseHandle(handle)

    def on_device_disconnected(self, device_path: str) -> None:
        try:
            self.close_and_remove_device(device_path.casefold())
        except Exception as ex:
            logging.warning(f'unable to close device {device_path} - ignoring device', exc_info=ex)

    def enumerate_present_devices(self) -> list[Device]:
        devices: list[Device] = []
        with DeviceInfoSet.of_present_devices(GUID_DEVINTERFACE_USB_DEVICE, None) as dev_info_set:
            hub_handles: dict[str, HANDLE] = {}
            try:
                while dev_info_set.next():
                    device = self.create_device_with_error_handler(dev_info_set, hub_handles)
                    if device is not None:
                        devices.append(device)
            finally:
                for handle in hub_handles.values():
                    kernel32.CloseHandle(handle)

        return devices

    def create_device_with_error_handler(self, dev_info_set: DeviceInfoSet, hub_handles: dict[str, HANDLE]
                                         ) -> Optional[Device]:
        instance_id = '<unknown>'
        try:
            instance_id = dev_info_set.get_string_property(DEVPKEY_Device_InstanceId)
            device_path = DeviceInfoSet.get_device_path(instance_id, GUID_DEVINTERFACE_USB_DEVICE)
            return self.create_device_from_device_info(dev_info_set, device_path, hub_handles)
        except Exception as ex:
            logging.exception(
                f'failed to retrieve information about device with instance ID {instance_id} - ignoring device',
                exc_info=ex)

    def create_device_from_device_info(self, dev_info_set: DeviceInfoSet, device_path: str,
                                       hub_handles: dict[str, HANDLE]) -> Device:
        usb_port_num = dev_info_set.get_int_property(DEVPKEY_Device_Address)
        parent_instance_id = dev_info_set.get_string_property(DEVPKEY_Device_Parent)
        hub_path = DeviceInfoSet.get_device_path(parent_instance_id, GUID_DEVINTERFACE_USB_HUB)

        hub_handle = hub_handles.get(hub_path)
        if hub_handle is None:
            hub_handle = kernel32.CreateFileW(hub_path, GENERIC_WRITE, FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None)
            if hub_handle == -1:
                raise_last_error('internal error (opening hub device)')
            hub_handles[hub_path] = hub_handle

        return self.create_device(device_path, dev_info_set.is_composite(), hub_handle, usb_port_num)

    def create_device(self, device_path: str, is_composite: bool, hub_handle: HANDLE, usb_port_num: int) -> Device:
        conn_info = USB_NODE_CONNECTION_INFORMATION_EX()
        conn_info.ConnectionIndex = usb_port_num
        size = DWORD()
        if kernel32.DeviceIoControl(hub_handle, IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX, byref(conn_info),
                                    sizeof(conn_info), byref(conn_info), sizeof(conn_info), byref(size),
                                    None) == 0:
            raise_last_error('internal error (getting device descriptor failed)')

        device_desc = conn_info.DeviceDescriptor
        config_desc = self.get_descriptor(hub_handle, usb_port_num, 2, 0, 0)

        device = WindowsDevice(device_path, is_composite, bytes(device_desc), config_desc)
        device.vid = device_desc.idVendor
        device.pid = device_desc.idProduct
        languages = self.get_languages(hub_handle, usb_port_num)
        device.manufacturer = self.get_string_descriptor(hub_handle, usb_port_num, device_desc.iManufacturer, languages)
        device.product = self.get_string_descriptor(hub_handle, usb_port_num, device_desc.iProduct, languages)
        device.serial = self.get_string_descriptor(hub_handle, usb_port_num, device_desc.iSerialNumber, languages)
        return device

    def get_languages(self, hub_handle: HANDLE, usb_port_num: int) -> [int]:
        try:
            langs = self.get_descriptor(hub_handle, usb_port_num, 3, 0, 0)
            num_langs = (len(langs) - 2) // 2
            return struct.unpack(f'<{num_langs}H', langs[2:])
        except WindowsError:
            return [0x0409]

    def get_string_descriptor(self, hub_handle: HANDLE, usb_port_num: int, index: int, languages: [int]) -> Optional[str]:
        if index == 0:
            return None

        desc: Optional[bytes] = None
        for lang_id in languages:
            try:
               desc = self.get_descriptor(hub_handle, usb_port_num, 3, index, lang_id)
               break
            except WindowsError:
                pass  # continue with next

        if desc is None:
            return None  # ignore missing string descriptor

        byte_end = len(desc) // 2 * 2  # round to multiple of 2
        return desc[2:byte_end].decode('utf-16')

    def get_descriptor(self, hub_handle: HANDLE, usb_port_num: int, descriptor_type: int, index: int,
                       language_id: int, descriptor_size: int = 0) -> bytes:
        request_data_offset = sizeof(ULONG) + sizeof(SetupPacket)
        initial_descriptor_size = descriptor_size if descriptor_size != 0 else 256
        size = initial_descriptor_size + request_data_offset

        request = USB_DESCRIPTOR_REQUEST()
        if sizeof(request) < size:
            resize(request, size)

        request.ConnectionIndex = usb_port_num
        setup_packet = request.setupPacket
        setup_packet.bmRequest = 0x80  # device-to-host / type standard / recipient device
        setup_packet.bRequest = 6  # GET_DESCRIPTOR
        setup_packet.wValue = (descriptor_type << 8) | index
        setup_packet.wIndex = language_id
        setup_packet.wLength = initial_descriptor_size

        effective_size = DWORD()
        if kernel32.DeviceIoControl(hub_handle, IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION, byref(request),
                                    size, byref(request), size, byref(effective_size), None) == 0:
            raise_last_error(f'internal error (retrieving descriptor {index} failed)')

        # determine size of descriptor
        if descriptor_type == 2:
            # total length of configuration descriptor
            expected_size = request.Data[2] + 256 * request.Data[3]
        else:
            # length byte of descriptor
            expected_size = request.Data[0]

        # check against effective size
        if effective_size.value - request_data_offset != expected_size:
            if descriptor_size != 0:
                raise USBError('internal error (unexpected descriptor size)')

            return self.get_descriptor(hub_handle, usb_port_num, descriptor_type, index, language_id, expected_size)

        return bytes(request)[request_data_offset:request_data_offset + expected_size]
