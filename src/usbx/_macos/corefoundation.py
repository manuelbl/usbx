# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from ctypes import POINTER, c_bool, c_char_p, c_int32, c_long, c_uint16, c_ulong, cdll, util, c_void_p, Structure, \
    c_ubyte, c_int
from ctypes import c_long as CFIndex
from ctypes import c_void_p as CFTypeRef


class CFUUIDBytes(Structure):
    _fields_ = [
        ('byte0', c_ubyte),
        ('byte1', c_ubyte),
        ('byte2', c_ubyte),
        ('byte3', c_ubyte),
        ('byte4', c_ubyte),
        ('byte5', c_ubyte),
        ('byte6', c_ubyte),
        ('byte7', c_ubyte),
        ('byte8', c_ubyte),
        ('byte9', c_ubyte),
        ('byte10', c_ubyte),
        ('byte11', c_ubyte),
        ('byte12', c_ubyte),
        ('byte13', c_ubyte),
        ('byte14', c_ubyte),
        ('byte15', c_ubyte),
    ]


class CFRange(Structure):
    _fields_ = [
        ('location', CFIndex),
        ('length', CFIndex),
    ]


def create_lib():
    lib = cdll.LoadLibrary(util.find_library('CoreFoundation'))

    lib.CFUUIDCreateFromUUIDBytes.argtypes = [c_void_p, CFUUIDBytes]
    lib.CFUUIDCreateFromUUIDBytes.restype = CFTypeRef

    lib.CFUUIDGetUUIDBytes.argtypes = [CFTypeRef]
    lib.CFUUIDGetUUIDBytes.restype = CFUUIDBytes

    lib.CFGetTypeID.argtypes = [CFTypeRef]
    lib.CFGetTypeID.restype = c_ulong

    lib.CFNumberGetTypeID.argtypes = []
    lib.CFNumberGetTypeID.restype = c_ulong

    lib.CFStringGetTypeID.argtypes = []
    lib.CFStringGetTypeID.restype = c_ulong

    lib.CFNumberGetValue.argtypes = [CFTypeRef, c_long, c_void_p]
    lib.CFNumberGetValue.restype = c_bool

    lib.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_int32]
    lib.CFStringCreateWithCString.restype = CFTypeRef

    lib.CFShow.argtypes = [CFTypeRef]
    lib.CFShow.restype = None

    lib.CFStringGetCStringPtr.argtypes = [CFTypeRef, c_int32]
    lib.CFStringGetCStringPtr.restype = c_char_p

    lib.CFStringGetLength.argtypes = [CFTypeRef]
    lib.CFStringGetLength.restype = CFIndex

    lib.CFStringGetCharacters.argtypes = [CFTypeRef, CFRange, POINTER(c_uint16)]
    lib.CFStringGetCharacters.restype = None

    lib.CFRunLoopGetCurrent.argtypes = []
    lib.CFRunLoopGetCurrent.restype = c_void_p

    lib.CFRunLoopAddSource.argtypes = [c_void_p, c_void_p, CFTypeRef]
    lib.CFRunLoopAddSource.restype = None

    lib.kCFRunLoopDefaultMode = CFTypeRef.in_dll(lib, 'kCFRunLoopDefaultMode')

    lib.CFRunLoopRun.argtypes = []
    lib.CFRunLoopRun.restype = None

    lib.mach_error_string.argtypes = [c_int]
    lib.mach_error_string.restype = c_char_p

    return lib


corefoundation = create_lib()

kCFNumberSInt32Type = 3
kCFStringEncodingASCII = 0x0600
kCFStringEncodingUTF8 = 0x08000100


def from_cf_string(cf_str: CFTypeRef) -> str:
    """
    Converts the CoreFoundation string ``cf_str`` to a Python string.
    
    :param cf_str: CoreFoundation string.
    :return: Python Unicode string.
    """
    cstr = corefoundation.CFStringGetCStringPtr(cf_str, kCFStringEncodingUTF8)
    if cstr:
        return cstr.decode('utf-8')

    length = corefoundation.CFStringGetLength(cf_str)
    buf = bytearray(length * 2)
    ctypes_buf = (c_uint16 * length).from_buffer(buf)
    char_range = CFRange(0, length)
    corefoundation.CFStringGetCharacters(cf_str, char_range, ctypes_buf)
    return buf.decode('utf-16')


def to_cf_string(string: str) -> CFTypeRef:
    """
    Converts the Python string ``string`` to a CoreFoundation string.

    :param string: Python Unicode string.
    :return:  CFStringRef object.
    """
    return corefoundation.CFStringCreateWithCString(None, string.encode('utf-8'), kCFStringEncodingUTF8)


def mach_error_message(error_code: c_int) -> str:
    msg = corefoundation.mach_error_string(error_code)
    return msg.decode("utf-8") if msg is not None else 'unknown error'
