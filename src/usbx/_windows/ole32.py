# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import ctypes
import uuid
from ctypes import HRESULT, Structure, c_ulong, c_ushort, c_ubyte, POINTER
from ctypes.wintypes import LPCOLESTR


class GUID(Structure):
    _fields_ = [
        ('Data1', c_ulong),
        ('Data2', c_ushort),
        ('Data3', c_ushort),
        ('Data4', c_ubyte * 8)
    ]

    def __init__(self, guid=None):
        super().__init__()
        if guid is not None:
            data = uuid.UUID(guid)
            self.Data1 = data.time_low
            self.Data2 = data.time_mid
            self.Data3 = data.time_hi_version
            self.Data4[0] = data.clock_seq_hi_variant
            self.Data4[1] = data.clock_seq_low
            self.Data4[2:] = data.node.to_bytes(6, 'big')

    def __repr__(self) -> str:
        guid = uuid.UUID(fields=(self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1],
                                 int.from_bytes(self.Data4[2:], 'big')))
        return str(guid)


PGUID = POINTER(GUID)
CLSID = GUID
PCLSID = POINTER(CLSID)


def create_lib():
    lib = ctypes.WinDLL('ole32', use_last_error=True)

    lib.CLSIDFromString.argtypes = [LPCOLESTR, PCLSID]
    lib.CLSIDFromString.restype = HRESULT

    return lib


ole32 = create_lib()
