# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from concurrent.futures import ThreadPoolExecutor
from time import sleep

from tests.base import TestBase
from usbx import TransferDirection, USBError


class TestAbort(TestBase):
    def test_abort(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)

        with ThreadPoolExecutor(max_workers=2) as executor:
            reader = executor.submit(self.read_bytes)
            sleep(0.2)
            self.test_device.abort_transfers(self.config.endpoint_loopback_in, TransferDirection.IN)
            reader.result(timeout=1)

    def read_bytes(self):
        try:
            self.test_device.transfer_in(self.config.endpoint_loopback_in)
            self.fail("unexpected success on transfer in")

        except USBError:
            pass  # expected

