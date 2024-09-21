# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from ctypes import cdll, c_void_p, c_int, c_char_p


def create_lib():
    lib = cdll.LoadLibrary('libudev.so.1')

    lib.udev_new.arg_types = []
    lib.udev_new.restype = c_void_p

    lib.udev_enumerate_new.argtypes = [c_void_p]
    lib.udev_enumerate_new.restype = c_void_p

    lib.udev_enumerate_unref.argtypes = [c_void_p]
    lib.udev_enumerate_unref.restype = c_void_p

    lib.udev_enumerate_add_match_subsystem.argtypes = [c_void_p, c_char_p]
    lib.udev_enumerate_add_match_subsystem.restype = c_int

    lib.udev_enumerate_scan_devices.argtypes = [c_void_p]
    lib.udev_enumerate_scan_devices.restype = c_int

    lib.udev_enumerate_get_list_entry.argtypes = [c_void_p]
    lib.udev_enumerate_get_list_entry.restype = c_void_p

    lib.udev_list_entry_get_next.argtypes = [c_void_p]
    lib.udev_list_entry_get_next.restype = c_void_p

    lib.udev_list_entry_get_name.argtypes = [c_void_p]
    lib.udev_list_entry_get_name.restype = c_char_p

    lib.udev_device_new_from_syspath.argtypes = [c_void_p, c_char_p]
    lib.udev_device_new_from_syspath.restype = c_void_p

    lib.udev_device_unref.argtypes = [c_void_p]
    lib.udev_device_unref.restype = c_void_p

    lib.udev_device_get_sysattr_value.argtypes = [c_void_p, c_char_p]
    lib.udev_device_get_sysattr_value.restype = c_char_p

    lib.udev_device_get_devnode.argtypes = [c_void_p]
    lib.udev_device_get_devnode.restype = c_char_p

    lib.udev_device_get_action.argtypes = [c_void_p]
    lib.udev_device_get_action.restype = c_char_p

    lib.udev_monitor_new_from_netlink.argtypes = [c_void_p, c_char_p]
    lib.udev_monitor_new_from_netlink.restype = c_void_p

    lib.udev_monitor_filter_add_match_subsystem_devtype.argtypes = [c_void_p, c_char_p]
    lib.udev_monitor_filter_add_match_subsystem_devtype.restype = c_int

    lib.udev_monitor_enable_receiving.argtypes = [c_void_p]
    lib.udev_monitor_enable_receiving.restype = c_int

    lib.udev_monitor_get_fd.argtypes = [c_void_p]
    lib.udev_monitor_get_fd.restype = c_int

    lib.udev_monitor_receive_device.argtypes = [c_void_p]
    lib.udev_monitor_receive_device.restype = c_void_p

    return lib


udev = create_lib()
