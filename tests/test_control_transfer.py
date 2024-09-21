# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import platform
from unittest import SkipTest

from tests.base import TestBase
from usbx import ControlTransfer, RequestType, Recipient, USBError


class TestControlTransfer(TestBase):

    def test_store_value(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x01, 0x29EA, self.config.interface_number)
        self.test_device.control_transfer_out(transfer)

    def test_retrieve_value(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x01, 0x9a41, self.config.interface_number)
        self.test_device.control_transfer_out(transfer)
        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x03, 0, self.config.interface_number)
        value_bytes = self.test_device.control_transfer_in(transfer, 4)

        expected_bytes = bytearray([0x41, 0x9a, 0x00, 0x00])
        self.assertEqual(value_bytes, expected_bytes)

    def test_store_value_data_stage(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        sent_values = bytearray([0x83, 0x03, 0xda, 0x3e])
        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x02, 0, self.config.interface_number)
        self.test_device.control_transfer_out(transfer, sent_values)
        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x03, 0, self.config.interface_number)
        retrieved_values = self.test_device.control_transfer_in(transfer, 4)
        self.assertEqual(retrieved_values, sent_values)

    def test_retrieve_interface_number(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x05, 0, self.config.interface_number)
        intf_number = self.test_device.control_transfer_in(transfer, 1)
        self.assertEqual(intf_number[0], self.config.interface_number)

        if self.config.is_composite:
            self.test_device.claim_interface(2)
            transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x05, 0, 2)
            intf_number = self.test_device.control_transfer_in(transfer, 1)
            self.assertEqual(intf_number[0], 2)

    def test_closed_device_fails(self):
        transfer = ControlTransfer(RequestType.STANDARD, Recipient.DEVICE, 0xee, 0, 0)
        with self.assertRaises(USBError):
            self.test_device.control_transfer_in(transfer, 255)
        with self.assertRaises(USBError):
            self.test_device.control_transfer_out(transfer)

    def test_unclaimed_interface_fails(self):
        self.test_device.open()
        transfer = ControlTransfer(RequestType.STANDARD, Recipient.INTERFACE, 0xee, 0, self.config.interface_number)
        with self.assertRaises(USBError):
            self.test_device.control_transfer_in(transfer, 255)
        with self.assertRaises(USBError):
            self.test_device.control_transfer_out(transfer)

    def test_get_configuration_descriptor(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        transfer = ControlTransfer(
            request_type=RequestType.STANDARD,
            recipient=Recipient.DEVICE,
            request=6,
            value=2 << 8,
            index=0,
        )
        desc = self.test_device.control_transfer_in(transfer, 1000)
        self.assertEqual(desc, self.test_device.configuration_descriptor)

    def test_no_interface_claimed(self):
        if platform.system() != 'Windows':
            raise SkipTest('Windows only test')

        self.test_device.open()
        transfer = ControlTransfer(
            request_type=RequestType.STANDARD,
            recipient=Recipient.DEVICE,
            request=6,
            value=2 << 8,
            index=0,
        )

        with self.assertRaises(USBError):
            self.test_device.control_transfer_in(transfer, 1000)
