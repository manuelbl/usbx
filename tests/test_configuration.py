# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from tests.base import TestBase
from usbx import TransferDirection, TransferType


class TestConfiguration(TestBase):

    def test_interface_descriptor(self):
        self.assertIsNotNone(self.test_device.configuration.interfaces)
        self.assertEqual(len(self.test_device.configuration.interfaces), self.config.interface_number + 1)

        intf = self.test_device.get_interface(self.config.interface_number)
        self.assertEqual(intf.number, self.config.interface_number)
        self.assertIsNotNone(intf.current_alternate)

    def test_invalid_interface_number(self):
        self.assertIsNone(self.test_device.get_interface(4))

    def test_alternate_interface_desc(self):
        intf = self.test_device.get_interface(self.config.interface_number)
        alt = intf.current_alternate
        self.assertIsNotNone(alt)
        self.assertIsNotNone(intf.alternates)
        self.assertEqual(len(intf.alternates), 1 if self.config.is_composite else 2)
        self.assertEqual(intf.alternates[0], alt)

        self.assertEqual(alt.class_code, 0xff)
        self.assertEqual(alt.subclass_code, 0x00)
        self.assertEqual(alt.protocol_code, 0x00)

        if not self.config.is_composite:
            alt = intf.alternates[1]
            self.assertEqual(alt.number, 1)

            self.assertEqual(alt.class_code, 0xff)
            self.assertEqual(alt.subclass_code, 0x00)
            self.assertEqual(alt.protocol_code, 0x00)

    def test_endpoint_desc(self):
        alt = self.test_device.get_interface(self.config.interface_number).current_alternate
        self.assertIsNotNone(alt.endpoints)
        self.assertEqual(len(alt.endpoints), 2 if self.config.is_composite else 4)

        endpoint = alt.endpoints[0]
        self.assertEqual(endpoint.number, 1)
        self.assertEqual(endpoint.direction, TransferDirection.OUT)
        self.assertEqual(endpoint.transfer_type, TransferType.BULK)
        self.assertTrue(endpoint.max_packet_size == 64 or endpoint.max_packet_size == 512)

        endpoint = alt.endpoints[1]
        self.assertEqual(endpoint.number, 2)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.BULK)
        self.assertTrue(endpoint.max_packet_size == 64 or endpoint.max_packet_size == 512)

        if not self.config.is_composite:
            endpoint = alt.endpoints[2]
            self.assertEqual(endpoint.number, 3)
            self.assertEqual(endpoint.direction, TransferDirection.OUT)
            self.assertEqual(endpoint.transfer_type, TransferType.INTERRUPT)
            self.assertEqual(endpoint.max_packet_size, 16)

            endpoint = alt.endpoints[3]
            self.assertEqual(endpoint.number, 3)
            self.assertEqual(endpoint.direction, TransferDirection.IN)
            self.assertEqual(endpoint.transfer_type, TransferType.INTERRUPT)
            self.assertEqual(endpoint.max_packet_size, 16)

            # test alternate interface 1
            alt = self.test_device.get_interface(self.config.interface_number).alternates[1]
            self.assertEqual(len(alt.endpoints), 2)

            endpoint = alt.endpoints[0]
            self.assertEqual(endpoint.number, 1)
            self.assertEqual(endpoint.direction, TransferDirection.OUT)
            self.assertEqual(endpoint.transfer_type, TransferType.BULK)
            self.assertTrue(endpoint.max_packet_size == 64 or endpoint.max_packet_size == 512)

            endpoint = alt.endpoints[1]
            self.assertEqual(endpoint.number, 2)
            self.assertEqual(endpoint.direction, TransferDirection.IN)
            self.assertEqual(endpoint.transfer_type, TransferType.BULK)
            self.assertTrue(endpoint.max_packet_size == 64 or endpoint.max_packet_size == 512)

    def test_invalid_endpoints(self):
        non_existent_endpoint = 4 if self.config.is_composite else 1
        self.assertIsNone(self.test_device.get_endpoint(non_existent_endpoint, TransferDirection.IN))
        self.assertIsNone(self.test_device.get_endpoint(4, TransferDirection.OUT))
        self.assertIsNone(self.test_device.get_endpoint(0, TransferDirection.IN))
        self.assertIsNone(self.test_device.get_endpoint(0, TransferDirection.OUT))
