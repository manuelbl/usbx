# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from concurrent.futures import ThreadPoolExecutor
from random import randbytes

from tests.base import TestBase
from usbx import TransferDirection


class TestBulkTransfer(TestBase):
    def test_small_transfer(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        test_data = randbytes(12)
        self.write_bytes(test_data)
        data = self.read_bytes(len(test_data))
        self.assertEqual(data, test_data)

    def test_medium_transfer(self):
        # This synchronous approach should work as the test device
        # has an internal buffer of about 500 bytes.
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        test_data = randbytes(140)
        self.write_bytes(test_data)
        data = self.read_bytes(len(test_data))
        self.assertEqual(data, test_data)

    def test_transfer_zlp(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        in_endpoint = self.test_device.get_endpoint(self.config.endpoint_loopback_in, TransferDirection.IN)
        test_data = randbytes(in_endpoint.max_packet_size)
        self.test_device.transfer_out(self.config.endpoint_loopback_out, test_data)
        self.test_device.transfer_out(self.config.endpoint_loopback_out, bytes())
        data = self.test_device.transfer_in(self.config.endpoint_loopback_in)
        self.assertEqual(data, test_data)
        data = self.test_device.transfer_in(self.config.endpoint_loopback_in)
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 0)

    def test_large_transfer(self):
        self.test_device.open()
        self.test_device.claim_interface(self.config.interface_number)
        num_bytes = 230763
        test_data = randbytes(num_bytes)

        with ThreadPoolExecutor(max_workers=2) as executor:
            writer = executor.submit(self.write_bytes, test_data)
            reader = executor.submit(self.read_bytes, num_bytes)
            data = reader.result(timeout=10)
            writer.result(timeout=2)
            self.assertEqual(data, test_data)

    def write_bytes(self, data: bytes) -> None:
        chunk_size = 100
        num_bytes = 0
        while num_bytes < len(data):
            size = min(len(data), chunk_size)
            self.test_device.transfer_out(self.config.endpoint_loopback_out, data[num_bytes:num_bytes + size])
            num_bytes += size

    def read_bytes(self, num_bytes: int) -> bytes:
        data = bytearray()
        while len(data) < num_bytes:
            chunk = self.test_device.transfer_in(self.config.endpoint_loopback_in)
            data.extend(chunk)
        return data
