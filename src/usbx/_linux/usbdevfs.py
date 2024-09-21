# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT


from ctypes import Structure, c_uint8, c_uint16, c_void_p, c_uint, c_int, c_char

from .ioctl import _IO, _IOR, _IOW, _IOWR

USBDEVFS_MAXDRIVERNAME: int = 255

class CtrlTransfer(Structure):
    _fields_ = [
        ('bmRequestType', c_uint8),
        ('bRequest', c_uint8),
        ('wValue', c_uint16),
        ('wIndex', c_uint16),
        ('wLength', c_uint16),
        ('timeout', c_uint),
        ('data', c_void_p),
    ]

class BulkTransfer(Structure):
    _fields_ = [
        ('ep', c_uint),
        ('len', c_uint),
        ('timeout', c_uint),
        ('data', c_void_p),
    ]

class SetInterface(Structure):
    _fields_ = [
        ('interface', c_uint),
        ('altsetting', c_uint),
    ]

class  DisconnectClaim(Structure):
    _fields_ = [
        ('interface', c_uint),
        ('flags', c_uint),
        ('driver', c_char * USBDEVFS_MAXDRIVERNAME)
    ]

class Urb(Structure):
    _fields_ = [
        ('type', c_uint8),
        ('endpoint', c_uint8),
        ('status', c_int),
        ('flags', c_uint),
        ('buffer', c_void_p),
        ('buffer_length', c_int),
        ('actual_length', c_int),
        ('start_frame', c_int),
        ('number_of_packets', c_int),
        ('error_count', c_int),
        ('signr', c_uint),
        ('usercontext', c_void_p),
    ]

class IoCtl(Structure):
    _fields_ = [
        ('ifno', c_uint),
        ('ioctl_code', c_uint),
        ('data', c_void_p),
    ]

    
USBDEVFS_URB_TYPE_ISO: int = 0
USBDEVFS_URB_TYPE_INTERRUPT: int = 1
USBDEVFS_URB_TYPE_CONTROL: int = 2
USBDEVFS_URB_TYPE_BULK: int = 3

USBDEVFS_DISCONNECT_CLAIM_EXCEPT_DRIVER: int = 0x02

USBDEVFS_CONTROL = _IOWR('U', 0, CtrlTransfer)
# USBDEVFS_CONTROL32 = _IOWR('U', 0, struct usbdevfs_ctrltransfer32)
USBDEVFS_BULK = _IOWR('U', 2, BulkTransfer)
# USBDEVFS_BULK32 = _IOWR('U', 2, struct usbdevfs_bulktransfer32)
USBDEVFS_RESETEP = _IOR('U', 3, c_uint)
USBDEVFS_SETINTERFACE = _IOR('U', 4, SetInterface)
# USBDEVFS_SETCONFIGURATION = _IOR('U', 5, unsigned int)
# USBDEVFS_GETDRIVER = _IOW('U', 8, struct usbdevfs_getdriver)
USBDEVFS_SUBMITURB = _IOR('U', 10, Urb)
# USBDEVFS_SUBMITURB32 = _IOR('U', 10, struct usbdevfs_urb32)
USBDEVFS_DISCARDURB = _IO('U', 11)
# USBDEVFS_REAPURB = _IOW('U', 12, void *)
# USBDEVFS_REAPURB32 = _IOW('U', 12, __u32)
USBDEVFS_REAPURBNDELAY = _IOW('U', 13, c_void_p)
# USBDEVFS_REAPURBNDELAY32 = _IOW('U', 13, __u32)
# USBDEVFS_DISCSIGNAL = _IOR('U', 14, struct usbdevfs_disconnectsignal)
# USBDEVFS_DISCSIGNAL32 = _IOR('U', 14, struct usbdevfs_disconnectsignal32)
USBDEVFS_CLAIMINTERFACE = _IOR('U', 15, c_uint)
USBDEVFS_RELEASEINTERFACE = _IOR('U', 16, c_uint)
# USBDEVFS_CONNECTINFO = _IOW('U', 17, struct usbdevfs_connectinfo)
USBDEVFS_IOCTL = _IOWR('U', 18, IoCtl)
# USBDEVFS_IOCTL32 = _IOWR('U', 18, struct usbdevfs_ioctl32)
# USBDEVFS_HUB_PORTINFO = _IOR('U', 19, struct usbdevfs_hub_portinfo)
# USBDEVFS_RESET = _IO('U', 20)
USBDEVFS_CLEAR_HALT = _IOR('U', 21, c_uint)
# USBDEVFS_DISCONNECT = _IO('U', 22)
USBDEVFS_CONNECT = _IO('U', 23)
# USBDEVFS_CLAIM_PORT = _IOR('U', 24, unsigned int)
# USBDEVFS_RELEASE_PORT = _IOR('U', 25, unsigned int)
# USBDEVFS_GET_CAPABILITIES = _IOR('U', 26, __u32)
USBDEVFS_DISCONNECT_CLAIM = _IOR('U', 27, DisconnectClaim)
# USBDEVFS_ALLOC_STREAMS = _IOR('U', 28, struct usbdevfs_streams)
# USBDEVFS_FREE_STREAMS = _IOR('U', 29, struct usbdevfs_streams)
# USBDEVFS_DROP_PRIVILEGES = _IOW('U', 30, __u32)
# USBDEVFS_GET_SPEED = _IO('U', 31)
