# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import ctypes
from ctypes import POINTER, Structure
from ctypes.wintypes import HWND, BOOL, DWORD, PDWORD, LPCWSTR as PCWSTR, WCHAR, WPARAM, HANDLE, ULONG, PWCHAR, \
    PBYTE, HKEY

from .ole32 import GUID, PGUID

ULONG_PTR = WPARAM


class HDEVINFO(HANDLE):
    pass


class SP_DEVINFO_DATA(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('ClassGuid', GUID),
        ('DevInst', DWORD),
        ('Reserved', ULONG_PTR)
    ]

    def __init__(self):
        super().__init__()
        self.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)


PSP_DEVINFO_DATA = POINTER(SP_DEVINFO_DATA)


class SP_DEVICE_INTERFACE_DATA(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('ClassGuid', GUID),
        ('Flags', DWORD),
        ('Reserved', ULONG_PTR)
    ]

    def __init__(self):
        super().__init__()
        self.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)


PSP_DEVICE_INTERFACE_DATA = POINTER(SP_DEVICE_INTERFACE_DATA)


class SP_DEVICE_INTERFACE_DETAIL_DATA_W(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('DevicePath', WCHAR * 260),
    ]

    def __init__(self):
        super().__init__()
        self.cbSize = 8  # expected by Windows for this variable size struct


PSP_DEVICE_INTERFACE_DETAIL_DATA_W = POINTER(SP_DEVICE_INTERFACE_DETAIL_DATA_W)


class DEVPROPKEY(Structure):
    _fields_ = [
        ('fmtid', GUID),
        ('pid', ULONG)
    ]


def create_lib() -> object:
    lib = ctypes.WinDLL('setupapi.dll', use_last_error=True)

    lib.SetupDiGetClassDevsW.argtypes = [PGUID, PWCHAR, HWND, DWORD]
    lib.SetupDiGetClassDevsW.restype = HDEVINFO

    lib.SetupDiEnumDeviceInfo.argtypes = [HDEVINFO, DWORD, PSP_DEVINFO_DATA]
    lib.SetupDiEnumDeviceInfo.restype = BOOL

    lib.SetupDiGetDevicePropertyW.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, POINTER(DEVPROPKEY), PDWORD, PBYTE, DWORD,
                                              PDWORD, DWORD]
    lib.SetupDiGetDevicePropertyW.restype = BOOL

    lib.SetupDiDeleteDeviceInterfaceData.argtypes = [HDEVINFO, PSP_DEVICE_INTERFACE_DATA]
    lib.SetupDiDeleteDeviceInterfaceData.restype = BOOL

    lib.SetupDiDestroyDeviceInfoList.argtypes = [HDEVINFO]
    lib.SetupDiDestroyDeviceInfoList.restype = BOOL

    lib.SetupDiEnumDeviceInterfaces.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, PGUID, DWORD, PSP_DEVICE_INTERFACE_DATA]
    lib.SetupDiEnumDeviceInterfaces.restype = BOOL

    lib.SetupDiGetDeviceInterfaceDetailW.argtypes = [HDEVINFO, PSP_DEVICE_INTERFACE_DATA,
                                                     PSP_DEVICE_INTERFACE_DETAIL_DATA_W, DWORD, PDWORD,
                                                     PSP_DEVINFO_DATA]
    lib.SetupDiGetDeviceInterfaceDetailW.restype = BOOL

    lib.SetupDiCreateDeviceInfoList.argtypes = [PGUID, HWND]
    lib.SetupDiCreateDeviceInfoList.restype = HDEVINFO

    lib.SetupDiOpenDeviceInterfaceW.argtypes = [HDEVINFO, PCWSTR, DWORD, PSP_DEVICE_INTERFACE_DATA]
    lib.SetupDiOpenDeviceInterfaceW.restype = BOOL

    lib.SetupDiOpenDeviceInfoW.argtypes = [HDEVINFO, PCWSTR, HWND, DWORD, PSP_DEVINFO_DATA]
    lib.SetupDiOpenDeviceInfoW.restype = BOOL

    lib.SetupDiOpenDevRegKey.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, DWORD, DWORD, DWORD, DWORD]
    lib.SetupDiOpenDevRegKey.restype = HKEY

    return lib


DIGCF_DEFAULT = 0x00000001
DIGCF_PRESENT = 0x00000002
DIGCF_ALLCLASSES = 0x00000004
DIGCF_PROFILE = 0x00000008
DIGCF_DEVICEINTERFACE = 0x00000010

DEVPROP_TYPE_STRING = 18
DEVPROP_TYPE_UINT32 = 7
DEVPROP_TYPEMOD_LIST = 8192

GUID_DEVINTERFACE_USB_DEVICE = GUID('{A5DCBF10-6530-11D2-901F-00C04FB951ED}')
GUID_DEVINTERFACE_USB_HUB = GUID('{f18a0e88-c30c-11d0-8815-00a0c906bed8}')

DEVPKEY_Device_HardwareIds: DEVPROPKEY = DEVPROPKEY(GUID('{a45c254e-df1c-4efd-8020-67d146a850e0}'), 3)  # NOSONAR
DEVPKEY_Device_Service: DEVPROPKEY = DEVPROPKEY(GUID('{a45c254e-df1c-4efd-8020-67d146a850e0}'), 6)
DEVPKEY_Device_Address: DEVPROPKEY = DEVPROPKEY(GUID('{a45c254e-df1c-4efd-8020-67d146a850e0}'), 30)
DEVPKEY_Device_InstanceId: DEVPROPKEY = DEVPROPKEY(GUID('{78c34fc8-104a-4aca-9ea4-524d52996e57}'), 256)
DEVPKEY_Device_Parent: DEVPROPKEY = DEVPROPKEY(GUID('{4340a6c5-93fa-4706-972c-7b648008a5a7}'), 8)
DEVPKEY_Device_Children: DEVPROPKEY = DEVPROPKEY(GUID('{4340a6c5-93fa-4706-972c-7b648008a5a7}'), 9)

DICS_FLAG_GLOBAL = 1
DIREG_DEV = 1

setupapi = create_lib()
