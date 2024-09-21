# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import ctypes
from ctypes import c_int, Structure, WINFUNCTYPE, POINTER, sizeof, c_wchar
from ctypes.wintypes import HICON, LPCWSTR, HBRUSH, HINSTANCE, UINT, HANDLE, HWND, WPARAM, LPARAM, ATOM, DWORD, HMENU, \
    LPVOID, BOOL, LPMSG

from .ole32 import GUID

LRESULT = LPARAM
WNDPROC = WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)


class WNDCLASSEXW(Structure):
    _fields_ = [
        ('cbSize', UINT),
        ('style', UINT),
        ('lpfnWndProc', WNDPROC),
        ('cbClsExtra', c_int),
        ('cbWndExtra', c_int),
        ('hinstance', HINSTANCE),
        ('hIcon', HICON),
        ('hCursor', HICON),
        ('hbrBackground', HBRUSH),
        ('lpszMenuName', LPCWSTR),
        ('lpszClassName', LPCWSTR),
        ('hIconSm', HICON)
    ]

    def __init__(self):
        super().__init__()
        self.cbSize = sizeof(self)


class DEV_BROADCAST_DEVICEINTERFACE_W(Structure):
    _fields_ = [
        ('dbcc_size', DWORD),
        ('dbcc_devicetype', DWORD),
        ('dbcc_reserved', DWORD),
        ('dbcc_classguid', GUID),
        ('dbcc_name', c_wchar),
    ]

    def __init__(self):
        super().__init__()
        self.dbcc_size = sizeof(self)


HWND_MESSAGE = HWND(-3)
DBT_DEVTYP_DEVICEINTERFACE = 5
DEVICE_NOTIFY_WINDOW_HANDLE = 0
WM_DEVICECHANGE = 537
DBT_DEVICEARRIVAL = 32768
DBT_DEVICEREMOVECOMPLETE = 32772


def create_lib() -> object:
    lib = ctypes.WinDLL('user32.dll', use_last_error=True)

    lib.RegisterClassExW.argtypes = [POINTER(WNDCLASSEXW)]
    lib.RegisterClassExW.restype = ATOM

    lib.CreateWindowExW.argtypes = [DWORD, LPCWSTR, LPCWSTR, DWORD, c_int, c_int, c_int, c_int, HWND, HMENU,
                                    HINSTANCE, LPVOID]
    lib.CreateWindowExW.restype = HWND

    lib.RegisterDeviceNotificationW.argtypes = [HANDLE, LPVOID, DWORD]
    lib.RegisterDeviceNotificationW.restype = HANDLE

    lib.GetMessageW.argtypes = [LPMSG, HWND, UINT, UINT]
    lib.GetMessageW.restype = BOOL

    lib.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    lib.DefWindowProcW.restype = LRESULT

    return lib


user32 = create_lib()
