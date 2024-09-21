# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from concurrent.futures import ThreadPoolExecutor
from random import randbytes

from tests.base import TestBase
from usbx import TransferDirection, USBError


class TestAlternate(TestBase):
    def test_select_alternate(self):
        if self.config.is_composite:
            self.skipTest("Test not supported by composite test device")

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        self.test_device.select_alternate(self.config.interface_number, 1)

        current_alternate = self.test_device.get_interface(self.config.interface_number).current_alternate
        self.assertEqual(current_alternate.number, 1)
        self.assertEqual(len(current_alternate.endpoints), 2)
        self.assertEqual(current_alternate.class_code, 0xff)

    def test_invalid_operations_fail(self):
        if self.config.is_composite:
            self.skipTest("Test not supported by composite test device")

        self.test_device.open()

        with self.assertRaises(USBError):
            self.test_device.select_alternate(1, 1)

        self.test_device.claim_interface(self.config.interface_number)

        with self.assertRaises(USBError):
            self.test_device.select_alternate(1, 0)

        with self.assertRaises(USBError):
            self.test_device.select_alternate(self.config.interface_number, 2)

    def test_transfer(self):
        if self.config.is_composite:
            self.skipTest("Test not supported by composite test device")

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        self.test_device.select_alternate(self.config.interface_number, 1)

        test_data = randbytes(12)
        self.test_device.transfer_out(self.config.endpoint_loopback_out, test_data)
        data = self.test_device.transfer_in(self.config.endpoint_loopback_in)
        self.assertEqual(data, test_data)

    def test_invalid_transfer_fails(self):
        if self.config.is_composite:
            self.skipTest("Test not supported by composite test device")

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        self.test_device.select_alternate(self.config.interface_number, 1)

        test_data = randbytes(12)
        with self.assertRaises(USBError):
            self.test_device.transfer_out(self.config.endpoint_echo_out, test_data)

        with self.assertRaises(USBError):
            self.test_device.transfer_in(self.config.endpoint_echo_in)
