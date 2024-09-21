# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from ctypes import c_void_p, byref, wintypes, cast, wstring_at, get_last_error, sizeof, create_string_buffer, c_char_p
from typing import Callable, Optional, Union
from winreg import KEY_READ, QueryValueEx, CloseKey

from .kernel32 import ERROR_NO_MORE_ITEMS, ERROR_NOT_FOUND, ERROR_INSUFFICIENT_BUFFER
from .ole32 import ole32, GUID, PGUID, CLSID
from .setupapi import setupapi, SP_DEVINFO_DATA, HDEVINFO, DIGCF_PRESENT, DIGCF_DEVICEINTERFACE, DEVPROP_TYPE_STRING, \
    SP_DEVICE_INTERFACE_DATA, SP_DEVICE_INTERFACE_DETAIL_DATA_W, DEVPROPKEY, DEVPROP_TYPE_UINT32, \
    DEVPKEY_Device_Service, DICS_FLAG_GLOBAL, DIREG_DEV, DEVPROP_TYPEMOD_LIST
from .winerror import raise_error, raise_last_error
from ..exceptions import USBError


def string_list_from_bytes(strlist: bytes) -> list[str]:
    string_list: list[str] = []
    start = 0
    index = 0
    while index + 1 < len(strlist):
        if strlist[index] == 0 and strlist[index + 1] == 0:
            if index == start:
                break
            string_list.append(wstring_at(strlist[start:index + 1]))
            start = index + 2
        index += 2
    return string_list


class DeviceInfoSet:
    """
    Device information set (of Windows Setup API).

    An instance of this class represents a device information set (``HDEVINFO``)
    and a current element within the set.
    """

    def __init__(self, create: Callable[[], Optional[HDEVINFO]]):
        self.dev_info_set: Optional[c_void_p] = create()
        if self.dev_info_set is None:
            raise USBError('internal error (creating device info set)')

        self.dev_info_data: SP_DEVINFO_DATA = SP_DEVINFO_DATA()
        self.dev_intf_data: Optional[SP_DEVICE_INTERFACE_DATA] = None
        self.iteration_index: int = -1

    def __del__(self):
        self.free_resources()

    def __enter__(self) -> 'DeviceInfoSet':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.free_resources()
        return False

    def free_resources(self):
        if self.dev_intf_data is not None:
            setupapi.SetupDiDeleteDeviceInterfaceData(self.dev_info_set, self.dev_intf_data)
            self.dev_intf_data = None
        if self.dev_info_set is not None:
            setupapi.SetupDiDestroyDeviceInfoList(self.dev_info_set)
            self.dev_info_set = None

    @classmethod
    def of_present_devices(cls, interface_guid: PGUID, instance_id: Optional[str]) -> 'DeviceInfoSet':
        def create_dev_info_set() -> Optional[HDEVINFO]:
            info_set = setupapi.SetupDiGetClassDevsW(byref(interface_guid), instance_id, None,
                                                     DIGCF_PRESENT | DIGCF_DEVICEINTERFACE)
            return info_set if info_set != -1 else None

        return DeviceInfoSet(create_dev_info_set)

    @classmethod
    def of_path(cls, device_path: str) -> 'DeviceInfoSet':
        device_info_set = DeviceInfoSet.of_empty()
        try:
            device_info_set.add_device_path(device_path)
            return device_info_set
        except Union[USBError, WindowsError]:
            device_info_set.free_resources()
            raise

    @classmethod
    def of_instance(cls, instance_id: str) -> 'DeviceInfoSet':
        device_info_set = DeviceInfoSet.of_empty()
        try:
            device_info_set.add_instance_id(instance_id)
            return device_info_set
        except Union[USBError, WindowsError]:
            device_info_set.free_resources()
            raise

    @classmethod
    def of_empty(cls) -> 'DeviceInfoSet':
        def empty_set() -> Optional[HDEVINFO]:
            info_set = setupapi.SetupDiCreateDeviceInfoList(None, None)
            return info_set if info_set != -1 else None

        return DeviceInfoSet(empty_set)

    @classmethod
    def get_device_path(cls, instance_id: str, interface_guid: GUID) -> str:
        """
        Gets the device path for the device with the given device instance ID and device interface class.

        :param instance_id: The device instance ID.
        :param interface_guid: The device interface guid.
        :return: The device path.
        """
        with DeviceInfoSet.of_present_devices(interface_guid, instance_id) as dev_info_set:
            return dev_info_set.get_device_path_for_guid(interface_guid)

    def next(self) -> bool:
        self.iteration_index += 1
        if setupapi.SetupDiEnumDeviceInfo(self.dev_info_set, self.iteration_index, byref(self.dev_info_data)) == 0:
            last_error = get_last_error()
            if last_error == ERROR_NO_MORE_ITEMS:
                return False
            raise_error(last_error, 'internal error (SetupDiEnumDeviceInfo)')
        return True

    def add_device_path(self, device_path: str) -> None:
        if self.dev_intf_data is not None:
            raise USBError('adding multiple paths to device info set is not supported')

        # load device information into dev info set
        intf_data = SP_DEVICE_INTERFACE_DATA()
        if setupapi.SetupDiOpenDeviceInterfaceW(self.dev_info_set, device_path, 0, intf_data) == 0:
            raise_last_error('internal error (SetupDiOpenDeviceInterfaceW)')

        self.dev_intf_data = intf_data

        if setupapi.SetupDiGetDeviceInterfaceDetailW(self.dev_info_set, intf_data, None, 0, None,
                                                     self.dev_info_data) == 0:
            last_error = get_last_error()
            if last_error != ERROR_INSUFFICIENT_BUFFER:
                raise_error(last_error, 'internal error (SetupDiGetDeviceInterfaceDetailW)')

    def add_instance_id(self, instance_id: str) -> None:
        if setupapi.SetupDiOpenDeviceInfoW(self.dev_info_set, instance_id, None, 0, self.dev_info_data) == 0:
            raise_last_error('internal error (SetupDiOpenDeviceInfoW)')

    def get_device_path_for_guid(self, interface_guid: GUID) -> Optional[str]:
        self.dev_intf_data = SP_DEVICE_INTERFACE_DATA()
        if setupapi.SetupDiEnumDeviceInterfaces(self.dev_info_set, None, byref(interface_guid), 0,
                                                byref(self.dev_intf_data)) == 0:
            raise_last_error('internal error (SetupDiEnumDeviceInterfaces)')

        detail_data = SP_DEVICE_INTERFACE_DETAIL_DATA_W()
        if setupapi.SetupDiGetDeviceInterfaceDetailW(self.dev_info_set, self.dev_intf_data, byref(detail_data),
                                                     sizeof(detail_data) - 4, None, None) == 0:
            raise_last_error('internal error (SetupDiGetDeviceInterfaceDetailW)')
        return wstring_at(detail_data.DevicePath)

    def get_device_path_by_guid(self, instance_id: str) -> Optional[str]:
        """
        Gets the device path for the device with the given instance ID.

        The device path is looked up in the registry by checking the GUIDs associated with the current element.

        :param instance_id: The device instance ID.
        :return: The device path.
        """
        guids = self.find_device_interface_guids()
        for guid in guids:
            clsid = CLSID()
            if ole32.CLSIDFromString(guid, byref(clsid)) != 0:
                continue

            try:
                return self.get_device_path(instance_id, clsid)
            except Union[USBError, WindowsError]:
                continue

        return None

    def find_device_interface_guids(self) -> list[str]:
        reg_key = setupapi.SetupDiOpenDevRegKey(self.dev_info_set, self.dev_info_data, DICS_FLAG_GLOBAL, 0, DIREG_DEV,
                                                KEY_READ)
        if reg_key == -1:
            raise_last_error('internal error (SetupDiOpenDevRegKey)')

        try:
            (value, _) = QueryValueEx(reg_key, 'DeviceInterfaceGUIDs')
            return value

        except FileNotFoundError:
            return []

        finally:
            CloseKey(reg_key)

    def get_string_property(self, property_key: DEVPROPKEY) -> str:
        """
        Gets the string device property of the current element.

        :param property_key: The property key (of type :class:`DEVPROPKEY`)
        :return: The property value
        """
        utf16_bytes = self.get_variable_length_property(property_key, DEVPROP_TYPE_STRING)
        return wstring_at(utf16_bytes)

    def get_string_list_property(self, property_key: DEVPROPKEY) -> Optional[list[str]]:
        """
        Gets the string list device property of the current element.

        :param property_key: The property key (of type :class:`DEVPROPKEY`)
        :return: The property value (list of strings)
        """
        property_value = self.get_variable_length_property(property_key, DEVPROP_TYPE_STRING | DEVPROP_TYPEMOD_LIST)
        if property_value is None:
            return None

        return string_list_from_bytes(bytes(property_value))

    def get_int_property(self, property_key: DEVPROPKEY) -> int:
        """
        Gets the integer device property of the current element.

        :param property_key: The property key (of type :class:`DEVPROPKEY`)
        :return: The property value
        """
        actual_property_type = wintypes.DWORD()
        property_value = wintypes.DWORD()
        if setupapi.SetupDiGetDevicePropertyW(self.dev_info_set, self.dev_info_data, byref(property_key),
                                              byref(actual_property_type), cast(byref(property_value), wintypes.PBYTE),
                                              sizeof(property_value), None, 0) == 0:
            raise_last_error('internal error (SetupDiGetDevicePropertyW - 3)')

        if actual_property_type.value != DEVPROP_TYPE_UINT32:
            raise USBError('internal error (unexpected property type - 3)')
        return property_value.value

    def get_variable_length_property(self, property_key: DEVPROPKEY, property_type: int) -> Optional[c_char_p]:
        actual_property_type = wintypes.DWORD()
        required_size = wintypes.DWORD()
        if setupapi.SetupDiGetDevicePropertyW(self.dev_info_set, self.dev_info_data, byref(property_key),
                                              byref(actual_property_type), None, 0, byref(required_size), 0) == 0:
            last_error = get_last_error()
            if last_error == ERROR_NOT_FOUND:
                return None
            if last_error != ERROR_INSUFFICIENT_BUFFER:
                raise_error(last_error, 'internal error(SetupDiGetDevicePropertyW)')

        if actual_property_type.value != property_type:
            raise USBError('internal error (unexpected property type)')

        buffer = create_string_buffer(required_size.value)

        if setupapi.SetupDiGetDevicePropertyW(self.dev_info_set, self.dev_info_data, byref(property_key),
                                              byref(actual_property_type), cast(buffer, wintypes.PBYTE),
                                              required_size.value, None, 0) == 0:
            raise_last_error('internal error (SetupDiGetDevicePropertyW - 2)')

        return buffer

    def is_composite(self) -> bool:
        device_service = self.get_string_property(DEVPKEY_Device_Service)
        return 'usbccgp'.casefold() == device_service.casefold()
