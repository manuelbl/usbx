# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from __future__ import annotations

import logging
from ctypes import byref, c_uint64, c_void_p, c_char_p
from typing import Callable, Optional

from .corefoundation import corefoundation as cf
from .iokit import get_property_as_int, get_property_as_string, iokit, io_object_t, get_plugin_interface, \
                   mach_port_t, IOUSBDeviceHandle, kIOUSBDeviceClassName,  kIOFirstMatchNotification, \
                   kIOTerminatedNotification
from .iokit import kIOUSBDeviceUserClientTypeID, kIOUSBDeviceInterfaceID187,  kUSBVendorID, kUSBProductID, \
    kUSBVendorString, kUSBProductString, kUSBSerialNumberString, IOUSBDeviceInterface187
from .macoserrors import check_result
from .macosdevice import MacosDevice
from .._common.registrybase import DeviceRegistryBase
from ..device import Device


def iterate_devices(iterator: io_object_t, to_device: Callable[[io_object_t, str],
                    Optional[Device]]) -> list[Device]:
    """
    Iterates ``iterator`` and returns the relevant :class:`Device` instances.
    :param iterator: IOKit iterator.
    :param to_device: Function taking an IOKit service and a IOKit entry ID string to create or
        lookup a :class:`Device` instance. The function may return ``None`` if device is not relevant.
    :return: List of :class:`Device` instances.
    """
    devices = []
    while True:
        service: io_object_t = iokit.IOIteratorNext(iterator)
        if service == 0:
            break

        try:
            # get entry ID
            entry_id = c_uint64()
            result = iokit.IORegistryEntryGetRegistryEntryID(service, byref(entry_id))
            if result != 0:
                continue

            device = to_device(service, str(entry_id.value))
            if device is not None:
                devices.append(device)

        finally:
            result = iokit.IOObjectRelease(service)
            check_result(result, 'Internal error (releasing IOKit service)')

    return devices


def setup_notification(notification_port: mach_port_t, notification_type: c_char_p,
                       callback_fn: Callable) -> io_object_t:
    """
    Sets up notifications to be informed about changes to the IOKit registry.
    :param notification_port: Mach port where notification is delivered to.
    :param notification_type: Type of notification to be informed about.
    :param callback_fn: Callback function to be called when a notification is received. The function takes
        a C ``void *`` (not supported) and an IOKit iterator. Also see Apple's documentation of
        ``IOServiceMatchingCallback``.
    :return:
    """
    matching_dict = iokit.IOServiceMatching(kIOUSBDeviceClassName)
    iterator = io_object_t()
    result = iokit.IOServiceAddMatchingNotification(
        notification_port,
        notification_type,
        matching_dict,
        callback_fn,
        None,
        byref(iterator)
    )
    check_result(result, 'Internal error (setting up notifications)')
    return iterator


def create_device(service: io_object_t, entry_id: str) -> Optional[Device]:
    """
    Creates a :class:`Device` instance for the given IOKit service.
    :param service: IOKit service.
    :param entry_id: Entry ID of USB device.
    :return: :class:`Device` instance, or ``None`` if device is not relevant.
    """
    # get interface for USB device
    intf: Optional[IOUSBDeviceHandle] = get_plugin_interface(service, kIOUSBDeviceUserClientTypeID,
                                                             kIOUSBDeviceInterfaceID187, IOUSBDeviceInterface187)
    if not intf:
        return None

    vendor_id = 0
    product_id = 0

    try:
        # get VID and PID
        vendor_id = get_property_as_int(service, kUSBVendorID)
        product_id = get_property_as_int(service, kUSBProductID)
        if vendor_id == 0 or product_id == 0:
            return None

        device = MacosDevice(intf, entry_id)
        device.vid = vendor_id
        device.pid = product_id

        # get additional properties
        device.manufacturer = get_property_as_string(service, kUSBVendorString)
        device.product = get_property_as_string(service, kUSBProductString)
        device.serial = get_property_as_string(service, kUSBSerialNumberString)

        return device

    except Exception as exception:
        logging.warning(f'unable to query device 0x{vendor_id:0x4}:0x{product_id:04x} - ignoring device',
                        exc_info=exception)

    finally:
        intf.contents.contents.Release(intf)


class MacosDeviceRegistry(DeviceRegistryBase):

    def monitor_devices(self) -> None:
        try:
            notification_port = iokit.IONotificationPortCreate(0)
            monitor_run_loop_source = iokit.IONotificationPortGetRunLoopSource(notification_port)
            monitor_run_loop = cf.CFRunLoopGetCurrent()
            cf.CFRunLoopAddSource(monitor_run_loop, monitor_run_loop_source, cf.kCFRunLoopDefaultMode)

            # setup notifications for connected devices
            device_connected_f = iokit.IOServiceMatchingCallback(self.device_connected)
            device_connected_iter = setup_notification(notification_port, kIOFirstMatchNotification,
                                                       device_connected_f)

            # iterate to activate notifications and get initial list of devices
            devices = iterate_devices(device_connected_iter, create_device)

            # setup notifications for disconnected devices
            device_disconnected_f = iokit.IOServiceMatchingCallback(self.device_disconnected)
            device_disconnected_iter = setup_notification(notification_port, kIOTerminatedNotification,
                                                          device_disconnected_f)

            # iterate to activate notifications
            iterate_devices(device_disconnected_iter, self.get_device)

            self.notify_enumeration_complete(devices)

        except Exception as exception:
            self.notify_enumeration_failed(exception)
            return

        cf.CFRunLoopRun()

        print("Done")  # should not get here

    def device_connected(self, refcon: c_void_p, iterator: io_object_t):
        new_devices = iterate_devices(iterator, create_device)
        for device in new_devices:
            self.add_device(device)

    def device_disconnected(self, refcon: c_void_p, iterator: io_object_t):
        try:
            removed_devices = iterate_devices(iterator, self.get_device)
            for device in removed_devices:
                self.close_and_remove_device(device.identifier)
        except Exception as exception:
            logging.warning('unable to close disconnected device - ignoring', exc_info=exception)

    def get_device(self, service: io_object_t, entry_id: str) -> Optional[Device]:
        for device in self.device_list:
            if device.identifier == entry_id:
                return device
        return None
