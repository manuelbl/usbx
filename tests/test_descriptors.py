# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from tests.base import TestBase


class TestDescriptors(TestBase):

    def test_device_descriptor(self):
        desc = self.test_device.device_descriptor
        self.assertEqual(len(desc), 18)
        self.assertEqual(desc[1], 0x01)

    def test_configuration_descriptor(self):
        desc = self.test_device.configuration_descriptor
        self.assertGreater(len(desc), 60)
        self.assertEqual(desc[1], 0x02)
