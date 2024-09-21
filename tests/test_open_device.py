# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from tests.base import TestBase
from usbx import USBError


class TestOpenDevice(TestBase):
    def test_open_close_device(self):
        self.assertFalse(self.test_device.is_open)

        self.test_device.open()
        self.assertTrue(self.test_device.is_open)

        self.test_device.close()
        self.assertFalse(self.test_device.is_open)

        self.test_device.close()
        self.assertFalse(self.test_device.is_open)

    def test_open_open_device(self):
        self.assertFalse(self.test_device.is_open)

        self.test_device.open()
        self.assertTrue(self.test_device.is_open)

        with self.assertRaises(USBError) as context:
            self.test_device.open()

        self.assertEqual(str(context.exception), "Device cannot be open for this operation")

    def test_claim_release_interface(self):
        interface_number = self.config.interface_number

        self.test_device.open()
        self.assertFalse(self.test_device.get_interface(interface_number).is_claimed)

        self.test_device.claim_interface(interface_number)
        self.assertTrue(self.test_device.get_interface(interface_number).is_claimed)

        self.test_device.release_interface(interface_number)
        self.assertFalse(self.test_device.get_interface(interface_number).is_claimed)

    def test_close_releases_interfaces(self):
        interface_number = self.config.interface_number

        self.test_device.open()
        self.assertFalse(self.test_device.get_interface(interface_number).is_claimed)

        self.test_device.claim_interface(interface_number)
        self.assertTrue(self.test_device.get_interface(interface_number).is_claimed)

        self.test_device.close()
        self.assertFalse(self.test_device.get_interface(interface_number).is_claimed)
