# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from __future__ import annotations

from ctypes import c_char_p as cstr_t, CDLL
from ctypes import c_int as kern_return_t
from ctypes import c_uint as io_object_t
from ctypes import c_uint as mach_port_t
from ctypes import c_uint32, c_uint64, cast, cdll, util, POINTER, byref, c_void_p, c_int32, Structure, CFUNCTYPE, \
    c_ulong, c_uint8, c_char_p, c_uint16
from ctypes import c_void_p as CFTypeRef
from typing import Type, Optional

from .corefoundation import CFUUIDBytes, corefoundation, kCFNumberSInt32Type, to_cf_string, from_cf_string


class IUnknown(Structure):
    pass


IUnknown._fields_ = [
    ('_reserved', c_void_p),
    ('QueryInterface', CFUNCTYPE(c_ulong, POINTER(POINTER(IUnknown)), CFUUIDBytes,
                                 POINTER(POINTER(POINTER(IUnknown))))),
    ('AddRef', CFUNCTYPE(c_ulong, POINTER(POINTER(IUnknown)))),
    ('Release', CFUNCTYPE(c_ulong, POINTER(POINTER(IUnknown))))
]

IUnknownHandle = POINTER(POINTER(IUnknown))


class IOUSBFindInterfaceRequest(Structure):
    _fields_ = [
        ('bInterfaceClass', c_uint16),
        ('bInterfaceSubClass', c_uint16),
        ('bInterfaceProtocol', c_uint16),
        ('bAlternateSetting', c_uint16),
    ]


class IOUSBDevRequest(Structure):
    _fields_ = [
        ('bmRequestType', c_uint8),
        ('bRequest', c_uint8),
        ('wValue', c_uint16),
        ('wIndex', c_uint16),
        ('wLength', c_uint16),
        ('pData', c_void_p),
        ('wLenDone', c_uint32),
    ]


class IOUSBDeviceInterface187(Structure):
    pass


IOUSBDeviceHandle = POINTER(POINTER(IOUSBDeviceInterface187))


class USBConfigurationDescriptor(Structure):
    """USB configuration descriptor"""
    _fields_ = [
        ('bLength', c_uint8),
        ('bDescriptorType', c_uint8),
        ('wTotalLength', c_uint16),
        ('bNumInterfaces', c_uint8),
        ('bConfigurationValue', c_uint8),
        ('iConfiguration', c_uint8),
        ('bmAttributes', c_uint8),
        ('maxPower', c_uint8),
    ]
    _pack_ = 1


IOUSBDeviceInterface187._fields_ = [
    ('_reserved', c_void_p),
    ('QueryInterface', CFUNCTYPE(c_ulong, IOUSBDeviceHandle, CFUUIDBytes, IUnknownHandle)),
    ('AddRef', CFUNCTYPE(c_ulong, IOUSBDeviceHandle)),
    ('Release', CFUNCTYPE(c_ulong, IOUSBDeviceHandle)),
    ('_reserved1', c_void_p),  # IOReturn (* CreateDeviceAsyncEventSource)(void* self, CFRunLoopSourceRef* source);
    ('_reserved2', c_void_p),  # CFRunLoopSourceRef (* GetDeviceAsyncEventSource)(void* self);
    ('_reserved3', c_void_p),  # IOReturn (* CreateDeviceAsyncPort)(void* self, mach_port_t* port);
    ('_reserved4', c_void_p),  # mach_port_t (* GetDeviceAsyncPort)(void* self);
    ('_reserved5', c_void_p),  # IOReturn (* USBDeviceOpen)(void* self);
    ('USBDeviceClose', CFUNCTYPE(c_ulong, IOUSBDeviceHandle)),
    ('_reserved7', c_void_p),  # IOReturn (* GetDeviceClass)(void* self, UInt8* devClass);
    ('_reserved8', c_void_p),  # IOReturn (* GetDeviceSubClass)(void* self, UInt8* devSubClass);
    ('_reserved9', c_void_p),  # IOReturn (* GetDeviceProtocol)(void* self, UInt8* devProtocol);
    ('_reserved10', c_void_p),  # IOReturn (* GetDeviceVendor)(void* self, UInt16* devVendor);
    ('_reserved11', c_void_p),  # IOReturn (* GetDeviceProduct)(void* self, UInt16* devProduct);
    ('_reserved12', c_void_p),  # IOReturn (* GetDeviceReleaseNumber)(void* self, UInt16* devRelNum);
    ('_reserved13', c_void_p),  # IOReturn (* GetDeviceAddress)(void* self, USBDeviceAddress* addr);
    ('_reserved14', c_void_p),  # IOReturn (* GetDeviceBusPowerAvailable)(void* self, UInt32* powerAvailable);
    ('_reserved15', c_void_p),  # IOReturn (* GetDeviceSpeed)(void* self, UInt8* devSpeed);
    ('_reserved16', c_void_p),  # IOReturn (* GetNumberOfConfigurations)(void* self, UInt8* numConfig);
    ('_reserved17', c_void_p),  # IOReturn (* GetLocationID)(void* self, UInt32* locationID);
    ('GetConfigurationDescriptorPtr', CFUNCTYPE(c_ulong, IOUSBDeviceHandle, c_uint8,
                                                POINTER(POINTER(USBConfigurationDescriptor)))),
    ('_reserved19', c_void_p),  # IOReturn (* GetConfiguration)(void* self, UInt8* configNum);
    ('SetConfiguration', CFUNCTYPE(c_ulong, IOUSBDeviceHandle, c_uint8)),
    ('_reserved21', c_void_p),  # IOReturn (* GetBusFrameNumber)(void* self, UInt64* frame, AbsoluteTime* atTime);
    ('_reserved22', c_void_p),  # IOReturn (* ResetDevice)(void* self);
    ('DeviceRequest', CFUNCTYPE(c_ulong, IOUSBDeviceHandle, POINTER(IOUSBDevRequest))),
    ('_reserved24', c_void_p),
    # IOReturn (* DeviceRequestAsync)(void* self, IOUSBDevRequest* req, IOAsyncCallback1 callback, void* refCon);
    ('CreateInterfaceIterator', CFUNCTYPE(c_ulong, IOUSBDeviceHandle, POINTER(IOUSBFindInterfaceRequest),
                                          POINTER(io_object_t))),
    ('USBDeviceOpenSeize', CFUNCTYPE(c_ulong, IOUSBDeviceHandle)),
    ('_reserved27', c_void_p),  # IOReturn (* DeviceRequestTO)(void* self, IOUSBDevRequestTO* req);
    ('_reserved28', c_void_p),
    # IOReturn (* DeviceRequestAsyncTO)(void* self, IOUSBDevRequestTO* req, IOAsyncCallback1 callback, void* refCon);
    ('_reserved29', c_void_p),  # IOReturn (* USBDeviceSuspend)(void* self, Boolean suspend);
    ('_reserved30', c_void_p),  # IOReturn (* USBDeviceAbortPipeZero)(void* self);
    ('_reserved31', c_void_p),  # IOReturn (* USBGetManufacturerStringIndex)(void* self, UInt8* msi);
    ('_reserved32', c_void_p),  # IOReturn (* USBGetProductStringIndex)(void* self, UInt8* psi);
    ('_reserved33', c_void_p),  # IOReturn (* USBGetSerialNumberStringIndex)(void* self, UInt8* snsi);
    ('USBDeviceReEnumerate', CFUNCTYPE(c_ulong, IOUSBDeviceHandle, c_uint32)),
]


class IOUSBInterfaceInterface190(Structure):
    pass


IOUSBInterfaceHandle = POINTER(POINTER(IOUSBInterfaceInterface190))


IOUSBInterfaceInterface190._fields_ = [
    ('_reserved', c_void_p),
    ('QueryInterface',
     CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, CFUUIDBytes, IUnknownHandle)),
    ('AddRef', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle)),
    ('Release', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle)),
    ('_reserved1', c_void_p),   # IOReturn (* CreateInterfaceAsyncEventSource)(void* self, CFRunLoopSourceRef* source);
    ('_reserved2', c_void_p),   # CFRunLoopSourceRef (* GetInterfaceAsyncEventSource)(void* self);
    ('_reserved3', c_void_p),   # IOReturn (* CreateInterfaceAsyncPort)(void* self, mach_port_t* port);
    ('_reserved4', c_void_p),   # mach_port_t (* GetInterfaceAsyncPort)(void* self);
    ('_reserved5', c_void_p),   # IOReturn (* USBInterfaceOpen)(void* self);
    ('USBInterfaceClose', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle)),
    ('_reserved7', c_void_p),   # IOReturn (* GetInterfaceClass)(void* self, UInt8* intfClass);
    ('_reserved8', c_void_p),   # IOReturn (* GetInterfaceSubClass)(void* self, UInt8* intfSubClass);
    ('_reserved9', c_void_p),   # IOReturn (* GetInterfaceProtocol)(void* self, UInt8* intfProtocol);
    ('_reserved10', c_void_p),   # IOReturn (* GetDeviceVendor)(void* self, UInt16* devVendor);
    ('_reserved11', c_void_p),   # IOReturn (* GetDeviceProduct)(void* self, UInt16* devProduct);
    ('_reserved12', c_void_p),   # IOReturn (* GetDeviceReleaseNumber)(void* self, UInt16* devRelNum);
    ('_reserved13', c_void_p),   # IOReturn (* GetConfigurationValue)(void* self, UInt8* configVal);
    ('GetInterfaceNumber', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, POINTER(c_uint8))),
    ('_reserved15', c_void_p),   # IOReturn (* GetAlternateSetting)(void* self, UInt8* intfAltSetting);
    ('GetNumEndpoints', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, POINTER(c_uint8))),
    ('_reserved17', c_void_p),   # IOReturn (* GetLocationID)(void* self, UInt32* locationID);
    ('_reserved18', c_void_p),   # IOReturn (* GetDevice)(void* self, io_service_t* device);
    ('SetAlternateInterface', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8)),
    ('_reserved20', c_void_p),   # IOReturn (* GetBusFrameNumber)(void* self, UInt64* frame, AbsoluteTime* atTime);
    ('_reserved21', c_void_p),   # IOReturn (* ControlRequest)(void* self, UInt8 pipeRef, IOUSBDevRequest* req);
    ('_reserved22', c_void_p),
    # IOReturn (* ControlRequestAsync)(void* self, UInt8 pipeRef, IOUSBDevRequest* req, IOAsyncCallback1 callback,
    #   void* refCon);
    ('GetPipeProperties', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8, POINTER(c_uint8), POINTER(c_uint8),
                                    POINTER(c_uint8), POINTER(c_uint16), POINTER(c_uint8))),
    ('_reserved24', c_void_p),   # IOReturn (* GetPipeStatus)(void* self, UInt8 pipeRef);
    ('AbortPipe', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8)),
    ('_reserved26', c_void_p),   # IOReturn (* ResetPipe)(void* self, UInt8 pipeRef);
    ('_reserved27', c_void_p),   # IOReturn (* ClearPipeStall)(void* self, UInt8 pipeRef);
    ('ReadPipe', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8, c_void_p, POINTER(c_uint32))),
    ('WritePipe', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8, c_void_p, c_uint32)),
    ('_reserved30', c_void_p),
    # IOReturn (* ReadPipeAsync)(void* self, UInt8 pipeRef, void* buf, UInt32 size, IOAsyncCallback1 callback,
    #   void* refcon);
    ('_reserved31', c_void_p),
    # IOReturn (* WritePipeAsync)(void* self, UInt8 pipeRef, void* buf, UInt32 size, IOAsyncCallback1 callback,
    #   void* refcon);
    ('_reserved32', c_void_p),
    # IOReturn (* ReadIsochPipeAsync)(void* self, UInt8 pipeRef, void* buf, UInt64 frameStart, UInt32 numFrames,
    #   IOUSBIsocFrame* frameList, IOAsyncCallback1 callback, void* refcon);
    ('_reserved33', c_void_p),
    # IOReturn (* WriteIsochPipeAsync)(void* self, UInt8 pipeRef, void* buf, UInt64 frameStart, UInt32 numFrames,
    #   IOUSBIsocFrame* frameList, IOAsyncCallback1 callback, void* refcon);
    ('_reserved34', c_void_p),   # IOReturn (* ControlRequestTO)(void* self, UInt8 pipeRef, IOUSBDevRequestTO* req);
    ('_reserved35', c_void_p),
    # IOReturn (* ControlRequestAsyncTO)(void* self, UInt8 pipeRef, IOUSBDevRequestTO* req, IOAsyncCallback1 callback,
    #   void* refCon);
    ('ReadPipeTO', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8, c_void_p, POINTER(c_uint32), c_uint32, c_uint32)),
    ('WritePipeTO', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8, c_void_p, c_uint32, c_uint32, c_uint32)),
    ('_reserved38', c_void_p),
    # IOReturn (* ReadPipeAsyncTO)(void* self, UInt8 pipeRef, void* buf, UInt32 size, UInt32 noDataTimeout,
    #   UInt32 completionTimeout, IOAsyncCallback1 callback, void* refcon);
    ('_reserved39', c_void_p),
    # IOReturn (* WritePipeAsyncTO)(void* self, UInt8 pipeRef, void* buf, UInt32 size, UInt32 noDataTimeout,
    #   UInt32 completionTimeout, IOAsyncCallback1 callback, void* refcon);
    ('_reserved40', c_void_p),   # IOReturn (* USBInterfaceGetStringIndex)(void* self, UInt8* si);
    ('USBInterfaceOpenSeize', CFUNCTYPE(c_ulong, IOUSBInterfaceHandle)),
    ('ClearPipeStallBothEnds',  CFUNCTYPE(c_ulong, IOUSBInterfaceHandle, c_uint8)),
    ('_reserved43', c_void_p),
    # IOReturn (* SetPipePolicy)(void* self, UInt8 pipeRef, UInt16 maxPacketSize, UInt8 maxInterval);
    ('_reserved44', c_void_p),   # IOReturn (* GetBandwidthAvailable)(void* self, UInt32* bandwidth);
    ('_reserved45', c_void_p),
    # IOReturn (* GetEndpointProperties)(void* self, UInt8 alternateSetting, UInt8 endpointNumber, UInt8 direction,
    # UInt8* transferType, UInt16* maxPacketSize, UInt8* interval);
]


def create_lib():
    lib = cdll.LoadLibrary(util.find_library('IOKit'))

    lib.IONotificationPortCreate.argtypes = [mach_port_t]
    lib.IONotificationPortCreate.restype = c_void_p

    lib.IONotificationPortGetRunLoopSource.argtypes = [c_void_p]
    lib.IONotificationPortGetRunLoopSource.restype = c_void_p

    lib.IOServiceMatching.argtypes = [cstr_t]
    lib.IOServiceMatching.restype = CFTypeRef

    lib.IOServiceGetMatchingServices.argtypes = [mach_port_t, CFTypeRef, POINTER(io_object_t)]
    lib.IOServiceGetMatchingServices.restype = kern_return_t

    lib.IOObjectRelease.argtypes = [io_object_t]
    lib.IOObjectRelease.restype = kern_return_t

    lib.IOIteratorNext.argtypes = [io_object_t]
    lib.IOIteratorNext.restype = io_object_t

    lib.IOCreatePlugInInterfaceForService.argtypes = [io_object_t, CFTypeRef, CFTypeRef, POINTER(IUnknownHandle),
                                                      POINTER(c_int32)]
    lib.IOCreatePlugInInterfaceForService.restype = kern_return_t

    lib.IORegistryEntryCreateCFProperty.argtypes = [io_object_t, CFTypeRef, c_void_p, c_uint32]
    lib.IORegistryEntryCreateCFProperty.restype = CFTypeRef

    lib.IORegistryEntryGetRegistryEntryID.argtypes = [io_object_t, POINTER(c_uint64)]
    lib.IORegistryEntryGetRegistryEntryID.restype = kern_return_t

    lib.IOServiceMatchingCallback = CFUNCTYPE(None, c_void_p, io_object_t)

    lib.IOServiceAddMatchingNotification.argtypes = [c_void_p, c_char_p, CFTypeRef, lib.IOServiceMatchingCallback,
                                                     c_void_p, POINTER(io_object_t)]
    lib.IOServiceAddMatchingNotification.restype = kern_return_t

    return lib


iokit: CDLL = create_lib()


def create_uuid(uuid_bytes: list[int]) -> CFTypeRef:
    cf_uuid_bytes = CFUUIDBytes(*uuid_bytes)
    return corefoundation.CFUUIDCreateFromUUIDBytes(None, cf_uuid_bytes)


kIOUSBDeviceClassName: bytes = b'IOUSBDevice'
kIOFirstMatchNotification: bytes = b'IOServiceFirstMatch'
kIOTerminatedNotification: bytes = b'IOServiceTerminate'
kIOUSBFindInterfaceDontCare: int = 0xffff
kIOUSBPipeStalled: int = 0xE000404F
kIOUSBTransactionTimeout: int = 0xE0004051
kIOReturnAborted: int = 0xE00002EB
kIOReturnExclusiveAccess: int = 0xE00002C5

kUSBReEnumerateCaptureDeviceMask: int = 1 << 30
kUSBReEnumerateReleaseDeviceMask: int = 1 << 29

kIOUSBDeviceUserClientTypeID: c_void_p = create_uuid(
    [0x9d, 0xc7, 0xb7, 0x80, 0x9e, 0xc0, 0x11, 0xD4, 0xa5, 0x4f, 0x00, 0x0a, 0x27, 0x05, 0x28, 0x61])
kIOUSBInterfaceUserClientTypeID: c_void_p = create_uuid(
    [0x2d, 0x97, 0x86, 0xc6, 0x9e, 0xf3, 0x11, 0xD4, 0xad, 0x51, 0x00, 0x0a, 0x27, 0x05, 0x28, 0x61])
kIOUSBDeviceInterfaceID187: c_void_p = create_uuid(
    [0x3C, 0x9E, 0xE1, 0xEB, 0x24, 0x02, 0x11, 0xB2, 0x8E, 0x7E, 0x00, 0x0A, 0x27, 0x80, 0x1E, 0x86])
kIOUSBInterfaceInterfaceID190: c_void_p = create_uuid(
    [0x8f, 0xdb, 0x84, 0x55, 0x74, 0xa6, 0x11, 0xD6, 0x97, 0xb1, 0x00, 0x30, 0x65, 0xd3, 0x60, 0x8e])
kIOCFPlugInInterfaceID: c_void_p = create_uuid(
    [0xC2, 0x44, 0xE8, 0x58, 0x10, 0x9C, 0x11, 0xD4, 0x91, 0xD4, 0x00, 0x50, 0xE4, 0xC6, 0x42, 0x6F])

kUSBVendorID: c_void_p = to_cf_string('idVendor')
kUSBProductID: c_void_p = to_cf_string('idProduct')
kUSBVendorString: c_void_p = to_cf_string('kUSBVendorString')
kUSBProductString: c_void_p = to_cf_string('kUSBProductString')
kUSBSerialNumberString: c_void_p = to_cf_string('kUSBSerialNumberString')


def get_plugin_interface(service: io_object_t, plugin_type: CFTypeRef, interface_id: CFTypeRef,
                         interface_type: Type) -> Optional[POINTER]:
    """
    Gets an interface of the IOKit service ``service``.

    :param service: The IOKit service.
    :param plugin_type: UUID specifying the plugin type (``CFUUIDRef``).
    :param interface_id: UUID specifying the interface ID (``CFUUIDRef``).
    :param interface_type: Python type of interface, e.g. :class:`IUnknown`.
    :return: Pointer to pointer to interface, or ``None`` if interface is not supported by the service.
    """
    plug = IUnknownHandle()
    score = c_int32(0)
    result = iokit.IOCreatePlugInInterfaceForService(service, plugin_type, kIOCFPlugInInterfaceID, byref(plug),
                                                     byref(score))
    if result != 0:
        return None

    intf = IUnknownHandle()
    result = plug.contents.contents.QueryInterface(plug, corefoundation.CFUUIDGetUUIDBytes(interface_id), byref(intf))
    plug.contents.contents.Release(plug)

    return cast(intf, POINTER(POINTER(interface_type))) if result == 0 and intf else None


def get_property_as_int(service: io_object_t, property_name: CFTypeRef) -> Optional[int]:
    """
    Gets the value of the numeric property ``property_name`` of the IOKit service ``service``.

    :param service: The IOKit service.
    :param property_name: The name of the property (``CFStringRef``).
    :return: The property value, or ``None`` if the property does not exist or is not a number.
    """

    iokit_prop = iokit.IORegistryEntryCreateCFProperty(service, property_name, None, 0)
    if iokit_prop is None:
        return None

    if corefoundation.CFGetTypeID(iokit_prop) != corefoundation.CFNumberGetTypeID():
        return None

    value = c_int32(0)
    corefoundation.CFNumberGetValue(iokit_prop, kCFNumberSInt32Type, byref(value))
    return value.value


def get_property_as_string(service: io_object_t, property_name: CFTypeRef) -> Optional[str]:
    """
    Gets the value of the string property ``property_name`` of the IOKit service ``service``.

    :param service: The IOKit service.
    :param property_name: The name of the property (``CFStringRef``).
    :return: The property value, or ``None`` if the property does not exist or is not a string.
    """
    iokit_prop = iokit.IORegistryEntryCreateCFProperty(service, property_name, None, 0)
    if iokit_prop is None:
        return None

    if corefoundation.CFGetTypeID(iokit_prop) != corefoundation.CFStringGetTypeID():
        return None

    return from_cf_string(iokit_prop)


class IOKitGuard(object):
    """
    Context manager to retain a reference to an IOKit object.

    Instance of this class can retain a reference to a single object.

    Use ``guard_iokit_object()`` to create instance of this class.
    """
    def __init__(self, handle: Optional[object] = None):
        self.handle: Optional[IUnknownHandle] = None
        if handle is not None:
            self.handle = cast(handle, IUnknownHandle)

    def __enter__(self):
        if self.handle is not None:
            self.handle.contents.contents.AddRef(self.handle)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle is not None:
            self.handle.contents.contents.Release(self.handle)
        return False

    def retain(self, handle: object) -> None:
        """
        Retains a reference to the specified IOKit object.

        The guard must not yet retain a reference to another object.

        :param handle: IOKit object handle
        """
        assert self.handle is None
        self.handle = cast(handle, IUnknownHandle)
        self.handle.contents.contents.AddRef(self.handle)


def guard_iokit_object(handle: Optional[object] = None) -> IOKitGuard:
    """
    Retains a reference to an IOKit object to guard it against being freed.
    The reference is released when the context ends.

    The IOKit object can be provided as a parameter to this function, or it can be
    added later using ``retain()``.

    It is designed to be used with the ``with`` keyword::

        with guard_iokit_object(iokit_object):
            ...

    Or::

        with guard_iokit_object() as guard:
            ...
            guard.retain(iokit_object)
            ...

    :param handle: Handle of IOKit object
    :return: :class:`IOKitGuard` instance
    """
    return IOKitGuard(handle)
