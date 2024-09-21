# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import unittest

from tests.configdescs import COMPOSITE_TEST_DEVICE, LARGE_COMPOSITE, SIMPLE
from usbx import TransferType, TransferDirection, USBError
from usbx._common import confparser


class TestConfigurationParser(unittest.TestCase):
    def test_simple_desc(self):
        configuration = confparser.USBConfigurationParser.parse_bytes(SIMPLE)
        self.assertEqual(len(configuration.interfaces), 1)

        interface = configuration.interfaces[0]
        self.assertEqual(interface.number, 0)
        self.assertEqual(len(interface.alternates), 1)

        alternate = interface.alternates[0]
        self.assertIs(interface.current_alternate, alternate)
        self.assertEqual(alternate.number, 0)
        self.assertEqual(len(alternate.endpoints), 0)
        self.assertEqual(alternate.class_code, 0x0ff)
        self.assertEqual(alternate.subclass_code, 0x0dd)
        self.assertEqual(alternate.protocol_code, 0x0cc)

        self.assertEqual(len(configuration.functions), 1)
        self.assertEqual(configuration.configuration_value, 1)
        self.assertEqual(configuration.attributes, 0x34)
        self.assertEqual(configuration.max_power, 0x64)

    def test_large_composite_desc(self):
        configuration = confparser.USBConfigurationParser.parse_bytes(LARGE_COMPOSITE)

        # 2 functions
        self.assertEqual(len(configuration.functions), 2)

        # function 0: 3 interfaces
        composite_function = configuration.functions[0]
        self.assertEqual(composite_function.first_intf_number, 0)
        self.assertEqual(composite_function.interface_count, 3)

        # function 1: 1 interface
        composite_function = configuration.functions[1]
        self.assertEqual(composite_function.first_intf_number, 3)
        self.assertEqual(composite_function.interface_count, 1)

        # 4 interfaces
        self.assertEqual(len(configuration.interfaces), 4)

        # interface 0
        interface = configuration.interfaces[0]
        self.assertEqual(interface.number, 0)
        self.assertEqual(len(interface.alternates), 1)
        alternate = interface.alternates[0]
        self.assertEqual(len(alternate.endpoints), 1)
        endpoint = alternate.endpoints[0]
        self.assertEqual(endpoint.number, 5)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.INTERRUPT)

        # interface 1
        interface = configuration.interfaces[1]
        self.assertEqual(interface.number, 1)
        self.assertEqual(len(interface.alternates), 2)
        alternate = interface.alternates[0]
        self.assertEqual(alternate.number, 0)
        self.assertEqual(len(alternate.endpoints), 0)
        alternate = interface.alternates[1]
        self.assertEqual(alternate.number, 1)
        self.assertEqual(len(alternate.endpoints), 1)
        endpoint = alternate.endpoints[0]
        self.assertEqual(endpoint.number, 1)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.ISOCHRONOUS)

        # interface 2
        interface = configuration.interfaces[2]
        self.assertEqual(interface.number, 2)
        self.assertEqual(len(interface.alternates), 2)
        alternate = interface.alternates[0]
        self.assertEqual(alternate.number, 0)
        self.assertEqual(len(alternate.endpoints), 0)
        alternate = interface.alternates[1]
        self.assertEqual(alternate.number, 1)
        self.assertEqual(len(alternate.endpoints), 1)
        endpoint = alternate.endpoints[0]
        self.assertEqual(endpoint.number, 2)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.ISOCHRONOUS)

        # interface 3
        interface = configuration.interfaces[3]
        self.assertEqual(interface.number, 3)
        self.assertEqual(len(interface.alternates), 1)
        alternate = interface.alternates[0]
        self.assertEqual(alternate.number, 0)
        self.assertEqual(len(alternate.endpoints), 1)
        endpoint = alternate.endpoints[0]
        self.assertEqual(endpoint.number, 4)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.INTERRUPT)

    def test_composite_test_device_desc(self):
        configuration = confparser.USBConfigurationParser.parse_bytes(COMPOSITE_TEST_DEVICE)

        # 2 functions
        self.assertEqual(len(configuration.functions), 2)

        # function 0: 2 interfaces
        composite_function = configuration.functions[0]
        self.assertEqual(composite_function.first_intf_number, 0)
        self.assertEqual(composite_function.interface_count, 2)

        # function 1: 2 interfaces
        composite_function = configuration.functions[1]
        self.assertEqual(composite_function.first_intf_number, 2)
        self.assertEqual(composite_function.interface_count, 2)

        # 4 interfaces
        self.assertEqual(len(configuration.interfaces), 4)

        # interface 0
        interface = configuration.interfaces[0]
        self.assertEqual(interface.number, 0)
        self.assertEqual(len(interface.alternates), 1)
        alternate = interface.alternates[0]
        self.assertEqual(len(alternate.endpoints), 1)
        endpoint = alternate.endpoints[0]
        self.assertEqual(endpoint.number, 3)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.INTERRUPT)

        # interface 1
        interface = configuration.interfaces[1]
        self.assertEqual(interface.number, 1)
        self.assertEqual(len(interface.alternates), 1)
        alternate = interface.alternates[0]
        self.assertEqual(len(alternate.endpoints), 2)
        endpoint = alternate.endpoints[0]
        self.assertEqual(endpoint.number, 2)
        self.assertEqual(endpoint.direction, TransferDirection.OUT)
        self.assertEqual(endpoint.transfer_type, TransferType.BULK)
        endpoint = alternate.endpoints[1]
        self.assertEqual(endpoint.number, 1)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.BULK)

        # interface 2
        interface = configuration.interfaces[2]
        self.assertEqual(interface.number, 2)
        self.assertEqual(len(interface.alternates), 1)
        alternate = interface.alternates[0]
        self.assertEqual(len(alternate.endpoints), 0)

        # interface 3
        interface = configuration.interfaces[3]
        self.assertEqual(interface.number, 3)
        self.assertEqual(len(interface.alternates), 1)
        alternate = interface.alternates[0]
        self.assertEqual(len(alternate.endpoints), 2)
        endpoint = alternate.endpoints[0]
        self.assertEqual(endpoint.number, 1)
        self.assertEqual(endpoint.direction, TransferDirection.OUT)
        self.assertEqual(endpoint.transfer_type, TransferType.BULK)
        endpoint = alternate.endpoints[1]
        self.assertEqual(endpoint.number, 2)
        self.assertEqual(endpoint.direction, TransferDirection.IN)
        self.assertEqual(endpoint.transfer_type, TransferType.BULK)

    def test_too_short_desc(self):
        desc = LARGE_COMPOSITE[:-1]

        with self.assertRaises(USBError) as context:
            confparser.USBConfigurationParser.parse_bytes(desc)

        self.assertEqual(str(context.exception), "Invalid USB configuration descriptor (invalid total length)")

    def test_too_long_desc(self):
        desc = LARGE_COMPOSITE + bytes([1])

        with self.assertRaises(USBError) as context:
            confparser.USBConfigurationParser.parse_bytes(desc)

        self.assertEqual(str(context.exception), "Invalid USB configuration descriptor (invalid total length)")

    def test_invalid_desc(self):
        desc = bytes([0x09, 0x41, 0x03, 0x07, 0x03, 0x07, 0x03, 0x07, 0x03, 0x07])

        with self.assertRaises(USBError) as context:
            confparser.USBConfigurationParser.parse_bytes(desc)

        self.assertEqual(str(context.exception), "Invalid USB configuration descriptor at pos 1")
