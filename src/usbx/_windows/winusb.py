# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import ctypes
from ctypes import Structure, POINTER, c_void_p
from ctypes.wintypes import ULONG, BYTE as UCHAR, USHORT, BOOLEAN, DWORD, HANDLE, BOOL, PULONG


class USB_DEVICE_DESCRIPTOR(Structure):
    _fields_ = [
        ('bLength', UCHAR),
        ('bDescriptorType', UCHAR),
        ('bcdUSB', USHORT),
        ('bDeviceClass', UCHAR),
        ('bDeviceSubClass', UCHAR),
        ('bDeviceProtocol', UCHAR),
        ('bMaxPacketSize0', UCHAR),
        ('idVendor', USHORT),
        ('idProduct', USHORT),
        ('bcdDevice', USHORT),
        ('iManufacturer', UCHAR),
        ('iProduct', UCHAR),
        ('iSerialNumber', UCHAR),
        ('bNumConfigurations', UCHAR),
    ]


class USB_NODE_CONNECTION_INFORMATION_EX(Structure):
    _fields_ = [
        ('ConnectionIndex', ULONG),
        ('DeviceDescriptor', USB_DEVICE_DESCRIPTOR),
        ('CurrentConfigurationValue', UCHAR),
        ('Speed', UCHAR),
        ('DeviceIsHub', BOOLEAN),
        ('DeviceAddress', USHORT),
        ('NumberOfOpenPipes', ULONG),
        ('ConnectionStatus', DWORD),
    ]


class SetupPacket(Structure):
    _fields_ = [
        ('bmRequest', UCHAR),
        ('bRequest', UCHAR),
        ('wValue', USHORT),
        ('wIndex', USHORT),
        ('wLength', USHORT),
    ]
    _pack_ = 1


class USB_DESCRIPTOR_REQUEST(Structure):
    _fields_ = [
        ('ConnectionIndex', ULONG),
        ('setupPacket', SetupPacket),
        ('Data', (UCHAR * 256))
    ]

class WINUSB_SETUP_PACKET(Structure):
    _fields_ = [
        ('RequestType', UCHAR),
        ('Request', UCHAR),
        ('Value', USHORT),
        ('Index', USHORT),
        ('Length', USHORT),
    ]


IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX = 0x220448

IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION = 0x220410

PIPE_TRANSFER_TIMEOUT = 0x03


WINUSB_INTERFACE_HANDLE = c_void_p
PWINUSB_INTERFACE_HANDLE = POINTER(WINUSB_INTERFACE_HANDLE)
PUCHAR = POINTER(UCHAR)


def create_lib():
    lib = ctypes.WinDLL('winusb.dll', use_last_error=True)

    lib.WinUsb_Initialize.argtypes = [HANDLE, PWINUSB_INTERFACE_HANDLE]
    lib.WinUsb_Initialize.restype = BOOL

    lib.WinUsb_GetAssociatedInterface.argtypes = [WINUSB_INTERFACE_HANDLE, UCHAR, PWINUSB_INTERFACE_HANDLE]
    lib.WinUsb_GetAssociatedInterface.restype = BOOL

    lib.WinUsb_Free.argtypes = [WINUSB_INTERFACE_HANDLE]
    lib.WinUsb_Free.restype = BOOL

    lib.WinUsb_ControlTransfer.argtypes = [WINUSB_INTERFACE_HANDLE, WINUSB_SETUP_PACKET, PUCHAR, ULONG, PULONG,
                                           c_void_p]
    lib.WinUsb_ControlTransfer.restype = BOOL

    lib.WinUsb_WritePipe.argtypes = [WINUSB_INTERFACE_HANDLE, UCHAR, PUCHAR, ULONG, PULONG, c_void_p]
    lib.WinUsb_WritePipe.restype = BOOL

    lib.WinUsb_ReadPipe.argtypes = [WINUSB_INTERFACE_HANDLE, UCHAR, PUCHAR, ULONG, PULONG, c_void_p]
    lib.WinUsb_ReadPipe.restype = BOOL

    lib.WinUsb_SetPipePolicy.argtypes = [WINUSB_INTERFACE_HANDLE, UCHAR, ULONG, ULONG, c_void_p]
    lib.WinUsb_SetPipePolicy.restype = BOOL

    lib.WinUsb_SetCurrentAlternateSetting.argtypes = [WINUSB_INTERFACE_HANDLE, UCHAR]
    lib.WinUsb_SetCurrentAlternateSetting.restype = BOOL

    lib.WinUsb_ResetPipe.argtypes = [WINUSB_INTERFACE_HANDLE, UCHAR]
    lib.WinUsb_ResetPipe.restype = BOOL

    lib.WinUsb_AbortPipe.argtypes = [WINUSB_INTERFACE_HANDLE, UCHAR]
    lib.WinUsb_AbortPipe.restype = BOOL

    return lib


winusb = create_lib()
