# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import logging
import select
from ctypes import c_void_p
from typing import Optional

from .linuxdevice import LinuxDevice
from .udev import udev
from .._common.registrybase import DeviceRegistryBase
from ..device import Device
from ..exceptions import USBError


def get_device_name(udev_device: c_void_p) -> Optional[str]:
    device_name = udev.udev_device_get_devnode(udev_device)
    return device_name.decode('utf8') if device_name is not None else None


def get_device_attribute(udev_device: c_void_p, attribute_name: bytes) -> Optional[str]:
    attribute_value = udev.udev_device_get_sysattr_value(udev_device, attribute_name)
    return attribute_value.decode('utf8') if attribute_value is not None else None


def get_device_action(udev_device: c_void_p) -> Optional[str]:
    action = udev.udev_device_get_action(udev_device)
    return action.decode('utf8') if action is not None else None


def get_device_details(udev_device: c_void_p) -> Optional[Device]:
    vid: int = 0
    pid: int = 0

    try:
        id_vendor = get_device_attribute(udev_device, b'idVendor')
        if id_vendor is None:
            return None

        id_product = get_device_attribute(udev_device, b'idProduct')
        if id_product is None:
            return None

        dev_path = get_device_name(udev_device)
        if dev_path is None:
            return None

        vid = int(id_vendor, 16)
        pid = int(id_product, 16)

        device = LinuxDevice(dev_path)
        device.vid = vid
        device.pid = pid
        device.manufacturer = get_device_attribute(udev_device, b'manufacturer')
        device.product = get_device_attribute(udev_device, b'product')
        device.serial = get_device_attribute(udev_device, b'serial')

        return device

    except Exception as ex:
        logging.exception(f'failed to retrieve information about device 0x{vid:04x}/0x{pid:04x} - ignoring device',
                          exc_info=ex)


def iterate_devices(udev_instance: c_void_p) -> list[Device]:
    devices: list[Device] = []
    udev_enum = udev.udev_enumerate_new(udev_instance)
    if udev_enum is None:
        raise USBError('internal error (udev_enumerate_new)')

    try:
        if udev.udev_enumerate_add_match_subsystem(udev_enum, b'usb') < 0:
            raise USBError('internal error (udev_enumerate_add_match_subsystem)')

        if udev.udev_enumerate_scan_devices(udev_enum) < 0:
            raise USBError('internal error (udev_enumerate_scan_devices)')

        entry = udev.udev_enumerate_get_list_entry(udev_enum)
        while entry is not None:
            path = udev.udev_list_entry_get_name(entry)
            if path is None:
                continue

            # get device handle
            dev = udev.udev_device_new_from_syspath(udev_instance, path)
            if dev is None:
                continue

            try:
                device = get_device_details(dev)
                if device is not None:
                    devices.append(device)

            finally:
                udev.udev_device_unref(dev)

            entry = udev.udev_list_entry_get_next(entry)

    finally:
        udev.udev_enumerate_unref(udev_enum)

    return devices


class LinuxDeviceRegistry(DeviceRegistryBase):
    def __init__(self):
        self.monitor_fd: int = -1
        self.udev_instance: Optional[c_void_p] = None
        self.monitor: Optional[c_void_p] = None
        super().__init__()

    def monitor_devices(self) -> None:
        self.udev_instance = udev.udev_new()
        if self.udev_instance is None:
            raise USBError('internal error (udev_new)')

        self.setup_monitor()

        devices = iterate_devices(self.udev_instance)
        self.notify_enumeration_complete(devices)

        self.poll_for_notifications()

    def setup_monitor(self) -> None:
        self.monitor = udev.udev_monitor_new_from_netlink(self.udev_instance, b'udev')
        if self.monitor is None:
            raise USBError('internal error (udev_monitor_new_from_netlink)')

        if udev.udev_monitor_filter_add_match_subsystem_devtype(self.monitor, b'usb', b'usb_device') < 0:
            raise USBError('internal error (udev_monitor_filter_add_match_subsystem_devtype)')

        if udev.udev_monitor_enable_receiving(self.monitor) < 0:
            raise USBError('internal error (udev_monitor_enable_receiving)')

        self.monitor_fd = udev.udev_monitor_get_fd(self.monitor)
        if self.monitor_fd < 0:
            raise USBError('internal error (udev_monitor_get_fd)')

    def poll_for_notifications(self) -> None:
        epoll = select.epoll()
        epoll.register(self.monitor_fd, select.EPOLLIN)

        while True:
            events = epoll.poll()
            for _, _ in events:
                device = udev.udev_monitor_receive_device(self.monitor)
                if device is not None:
                    try:
                        action = get_device_action(device)
                        if action == 'add':
                            self.device_connected(device)
                        elif action == 'remove':
                            self.device_disconnected(device)

                    finally:
                        udev.udev_device_unref(device)

    def device_connected(self, udev_device: c_void_p) -> None:
        device = get_device_details(udev_device)
        if device is not None:
            self.add_device(device)

    def device_disconnected(self, udev_device: c_void_p) -> None:
        dev_path = get_device_name(udev_device)
        if dev_path is not None:
            self.close_and_remove_device(dev_path)
