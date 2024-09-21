# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from tests.base import TestBase
from usbx import Version


class TestDeviceInfo(TestBase):

    def test_device_info(self):
        is_composite = self.config.is_composite
        self.assertEqual(self.test_device.vid, self.config.vid)
        self.assertEqual(self.test_device.pid, self.config.pid)
        self.assertEqual(self.test_device.manufacturer, 'JavaDoesUSB')
        self.assertEqual(self.test_device.product, 'Composite' if is_composite else 'Loopback')
        self.assertRegex(self.test_device.serial, r'^[A-F0-9]{12}$')
        self.assertGreater(len(self.test_device.identifier), 8)
        self.assertEqual(self.test_device.configuration_value, 1)
        self.assertEqual(len(self.test_device.device_descriptor), 18)
        self.assertGreater(len(self.test_device.configuration_descriptor), 30)
        self.assertEqual(self.test_device.class_code, 0xef if is_composite else 0xff)
        self.assertEqual(self.test_device.subclass_code, 0x02 if is_composite else 0x00)
        self.assertEqual(self.test_device.protocol_code, 0x01 if is_composite else 0x00)
        self.assertEqual(self.test_device.usb_version, Version(0x0210 if is_composite else 0x0200))
        self.assertEqual(self.test_device.device_version, Version(0x036 if is_composite else 0x0074))
        self.assertEqual(self.test_device.max_packet_size, 64)
