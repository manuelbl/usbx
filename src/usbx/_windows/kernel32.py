# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import ctypes
from ctypes import c_void_p
from ctypes.wintypes import LPCWSTR, DWORD, HANDLE, BOOL, LPVOID, LPDWORD, HMODULE


def create_lib() -> object:
    lib = ctypes.WinDLL('kernel32', use_last_error=True)

    lib.CreateFileW.argtypes = [LPCWSTR, DWORD, DWORD, c_void_p, DWORD, DWORD, HANDLE]
    lib.CreateFileW.restype = HANDLE

    lib.CloseHandle.argtypes = [HANDLE]
    lib.CreateFileW.restype = BOOL

    lib.DeviceIoControl.argtypes = [HANDLE, DWORD, LPVOID, DWORD, LPVOID, DWORD, LPDWORD, c_void_p]
    lib.DeviceIoControl.restype = BOOL

    lib.GetModuleHandleW.argtypes = [LPCWSTR]
    lib.GetModuleHandleW.restype = HMODULE

    return lib


ERROR_FILE_NOT_FOUND = 2
ERROR_INSUFFICIENT_BUFFER = 122
ERROR_NO_MORE_ITEMS = 259
ERROR_NOT_FOUND = 1168
ERROR_MORE_DATA = 234

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 128
FILE_FLAG_OVERLAPPED = 0x40000000

kernel32 = create_lib()
