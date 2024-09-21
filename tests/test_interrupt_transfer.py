# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from random import randbytes
from unittest import SkipTest

from tests.base import TestBase


class TestInterruptTransfer(TestBase):
    def test_small_transfer(self):
        if self.config.is_composite:
            raise SkipTest('composite device does not support interrupt transfers')

        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        test_data = randbytes(12)
        self.test_device.transfer_out(self.config.endpoint_echo_out, test_data)

        # first echo
        echo = self.test_device.transfer_in(self.config.endpoint_echo_in)
        self.assertEqual(echo, test_data)

        # second echo
        echo = self.test_device.transfer_in(self.config.endpoint_echo_in)
        self.assertEqual(echo, test_data)
