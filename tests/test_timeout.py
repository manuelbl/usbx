# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from random import randbytes
from unittest import SkipTest, skipIf

from usbx import TransferTimeoutError, TransferDirection
from tests.base import TestBase


class TestTimeout(TestBase):
    def test_bulk_transfer_in(self) -> None:
        def bulk_transfer_in() -> None:
            self.test_device.transfer_in(self.config.endpoint_loopback_in, timeout=0.2)

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        with self.assertRaises(TransferTimeoutError):
            self.run_with_timeout(1, bulk_transfer_in)

    def test_bulk_transfer_succeeds(self) -> None:
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        test_data = randbytes(20)
        self.test_device.transfer_out(self.config.endpoint_loopback_out, test_data, timeout=0.2)
        data = self.test_device.transfer_in(self.config.endpoint_loopback_in, timeout=0.2)
        self.assertEqual(data, test_data)

    def test_bulk_transfer_out(self) -> None:
        def bulk_transfer_out() -> None:
            for _ in range(buffer_size // len(data)):
                self.test_device.transfer_out(ep_out, data, 0.2)

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        ep_out = self.config.endpoint_loopback_out

        # The test device has an internal buffer of about 2KB for full-speed
        # and 16KB for high-speed. The first transfer should not time out.
        buffer_size = 32 * self.test_device.get_endpoint(ep_out, TransferDirection.OUT).max_packet_size
        data = randbytes(100)
        self.test_device.transfer_out(ep_out, data, timeout=0.2)

        with self.assertRaises(TransferTimeoutError):
            self.run_with_timeout(2, bulk_transfer_out)

    def test_interrupt_transfer_in(self) -> None:
        def interrupt_transfer_in() -> None:
            self.test_device.transfer_in(self.config.endpoint_echo_in, timeout=0.2)

        if self.config.is_composite:
            raise SkipTest('composite device does not support interrupt transfers')

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        with self.assertRaises(TransferTimeoutError):
            self.run_with_timeout(2, interrupt_transfer_in)

    def test_interrupt_transfer_succeeds(self) -> None:
        if self.config.is_composite:
            raise SkipTest('composite device does not support interrupt transfers')

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        test_data = randbytes(12)
        self.test_device.transfer_out(self.config.endpoint_echo_out, test_data, timeout=0.2)

        # first echo
        data = self.test_device.transfer_in(self.config.endpoint_echo_in, timeout=0.2)
        self.assertEqual(data, test_data)

        # second echo
        data = self.test_device.transfer_in(self.config.endpoint_echo_in, timeout=0.2)
        self.assertEqual(data, test_data)
