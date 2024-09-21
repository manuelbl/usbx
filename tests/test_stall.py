# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from random import randbytes

from tests.base import TestBase
from usbx import ControlTransfer, RequestType, Recipient, TransferDirection, StallError, Endpoint


class TestStall(TestBase):

    def test_transfer_out_clear(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        endpoint_in = self.config.endpoint_loopback_in
        endpoint_out = self.config.endpoint_loopback_out
        self.halt_endpoint(endpoint_out, TransferDirection.OUT)

        test_data = randbytes(10)
        with self.assertRaises(StallError):
            self.test_device.transfer_out(endpoint_out, test_data)

        self.test_device.clear_halt(endpoint_out, TransferDirection.OUT)

        self.test_device.transfer_out(endpoint_out, test_data)
        data = self.test_device.transfer_in(endpoint_in)
        self.assertEqual(data, test_data)

    def test_transfer_in_clear(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        endpoint_in = self.config.endpoint_loopback_in
        endpoint_out = self.config.endpoint_loopback_out
        self.halt_endpoint(endpoint_in, TransferDirection.IN)

        with self.assertRaises(StallError):
            self.test_device.transfer_in(endpoint_in)

        self.test_device.clear_halt(endpoint_in, TransferDirection.IN)

        test_data = randbytes(10)
        self.test_device.transfer_out(endpoint_out, test_data)
        data = self.test_device.transfer_in(endpoint_in)
        self.assertEqual(data, test_data)

    def test_invalid_control_transfer(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x08, 0, self.config.interface_number)
        with self.assertRaises(StallError):
            self.test_device.control_transfer_in(transfer, 2)

    def halt_endpoint(self, number: int, direction: TransferDirection) -> None:
        set_feature = 0x03
        endpoint_halt = 0x00
        address = Endpoint.get_address(number, direction)
        transfer = ControlTransfer(RequestType.STANDARD, Recipient.ENDPOINT, set_feature, endpoint_halt, address)
        self.test_device.control_transfer_out(transfer)
