# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from usbx import usb, Device
from tests.base import TestBase


def is_test_device(device: Device) -> bool:
    return device.vid == 0xcafe


class TestEnumeration(TestBase):
    def test_all_devices(self):
        devices = usb.get_devices()
        self.assertIn(self.test_device, devices)

    def test_find_devices_lambda(self):
        devices = usb.find_devices(is_test_device)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0], self.test_device)

    def test_find_devices_kwargs(self):
        devices = usb.find_devices(vid=self.config.vid, pid=self.config.pid)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0], self.test_device)

    def test_find_device_lambda(self):
        device = usb.find_device(is_test_device)
        self.assertEqual(device, self.test_device)

    def test_find_device_kwargs(self):
        device = usb.find_device(vid=self.config.vid, pid=self.config.pid)
        self.assertEqual(device, self.test_device)
