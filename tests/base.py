# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import unittest
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from tests.deviceconfig import get_config
from usbx import usb, Device, ControlTransfer, RequestType, Recipient, TransferTimeoutError


class TestBase(unittest.TestCase):

    def setUp(self):
        self.test_device: Device = usb.find_device(lambda device: get_config(device) is not None)
        if self.test_device is None:
            self.fail('No test device connected (required for most unit tests)')
        self.config = get_config(self.test_device)

    def tearDown(self):
        self.reset_device()
        self.test_device.close()

    def reset_device(self):
        if self.test_device.get_interface(self.config.interface_number).is_claimed:
            if not self.config.is_composite:
                self.test_device.select_alternate(self.config.interface_number, 0)

            self.reset_buffers()

            self.drain_endpoint(self.config.endpoint_loopback_in)
            if not self.config.is_composite:
                self.drain_endpoint(self.config.endpoint_echo_in)

            self.reset_buffers()

    def drain_endpoint(self, endpoint_number: int):
        try:
            while True:
                self.test_device.transfer_in(endpoint_number, timeout=0.001)
        except TransferTimeoutError:
            pass  # read until timeout occurs

    def reset_buffers(self):
        transfer = ControlTransfer(RequestType.VENDOR, Recipient.INTERFACE, 0x04, 0, self.config.interface_number)
        self.test_device.control_transfer_out(transfer)

    def run_with_timeout(self, timeout: int, fn: Callable[[], None]) -> None:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn)
            try:
                future.result(timeout=timeout)
            except TimeoutError:
                self.test_device.close()
                self.fail(f'Test did not finish after {timeout} seconds')
