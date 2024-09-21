# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from struct import Struct
from typing import Optional

from ..configuration import Configuration, AlternateInterface, Interface, CompositeFunction, Endpoint
from ..exceptions import USBError

device_descriptor_type = 0x01
configuration_descriptor_type = 0x02
string_descriptor_type = 0x03
interface_descriptor_type = 0x04
endpoint_descriptor_type = 0x05
interface_association_descriptor_type = 0x0b


class USBConfigurationParser(object):

    @classmethod
    def parse_bytes(cls, desc: bytes) -> Configuration:
        return USBConfigurationParser(desc).configuration

    def __init__(self, buffer: bytes):
        self.buffer = buffer
        self.uint16 = Struct('<H')
        self.configuration = self.parse_header()
        self.parse()

    def parse(self) -> None:
        last_alternate: Optional[AlternateInterface] = None
        offset = self.peek_desc_length(0)

        while offset < len(self.buffer):
            desc_length = self.peek_desc_length(offset)
            desc_type = self.peek_desc_type(offset)

            if offset + desc_length > len(self.buffer):
                raise USBError(f"Invalid USB configuration descriptor at pos {offset}")

            if desc_type == interface_descriptor_type:
                intf = self.parse_interface(offset)
                last_alternate = self.add_interface(intf)

            elif desc_type == endpoint_descriptor_type:
                endpoint = self.parse_endpoint(offset)
                if last_alternate is not None:
                    last_alternate.endpoints.append(endpoint)

            elif desc_type == interface_association_descriptor_type:
                self.parse_iad(offset)

            offset += desc_length

    #  struct USBConfigurationDescriptor {
    #      uint8_t  bLength;
    #      uint8_t  bDescriptorType;
    #      uint16_t wTotalLength;
    #      uint8_t  bNumInterfaces;
    #      uint8_t  bConfigurationValue;
    #      uint8_t  iConfiguration;
    #      uint8_t  bmAttributes;
    #      uint8_t  bMaxPower;
    #  } __attribute__((packed));

    def add_interface(self, intf: Interface) -> AlternateInterface:
        parent = self.configuration.get_interface(intf.number)
        if parent is not None:
            # additional alternate setting for interface
            parent.alternates.append(intf.current_alternate)
        else:
            # new interface
            self.configuration.interfaces.append(intf)

        last_alternate = intf.current_alternate

        composite_func = self.configuration.get_function(intf.number)
        if composite_func is None:
            # create composite function with a single interface
            composite_func = CompositeFunction(intf.number, 1, last_alternate.class_code,
                                               last_alternate.subclass_code, last_alternate.protocol_code)
            self.configuration.functions.append(composite_func)

        return last_alternate

    def parse_header(self) -> Configuration:
        if len(self.buffer) < 9:
            raise USBError("Invalid USB configuration descriptor (too short)")

        if self.buffer[0] != 9:
            raise USBError("Invalid USB configuration descriptor at pos 0")

        if self.buffer[1] != configuration_descriptor_type:
            raise USBError("Invalid USB configuration descriptor at pos 1")

        total_length = self.uint16.unpack_from(self.buffer, offset=2)[0]
        if total_length != len(self.buffer):
            raise USBError("Invalid USB configuration descriptor (invalid total length)")

        config = Configuration()
        config.configuration_value = self.buffer[5]
        config.attributes = self.buffer[7]
        config.max_power = self.buffer[8]
        return config

    #  struct USBInterfaceDescriptor {
    #      uint8_t bLength;
    #      uint8_t bDescriptorType;
    #      uint8_t bInterfaceNumber;
    #      uint8_t bAlternateSetting;
    #      uint8_t bNumEndpoints;
    #      uint8_t bInterfaceClass;
    #      uint8_t bInterfaceSubClass;
    #      uint8_t bInterfaceProtocol;
    #      uint8_t iInterface;
    #  } __attribute__((packed));

    def parse_interface(self, offset: int) -> Interface:
        alternate = AlternateInterface(
            self.buffer[offset + 3],
            self.buffer[offset + 5],
            self.buffer[offset + 6],
            self.buffer[offset + 7],
        )
        number = self.buffer[offset + 2]
        return Interface(number, [alternate])

    #  struct USBEndpointDescriptor {
    #      uint8_t bLength;
    #      uint8_t bDescriptorType;
    #      uint8_t bEndpointAddress;
    #      uint8_t bmAttributes;
    #      uint16_t wMaxPacketSize;
    #      uint8_t bInterval;
    #  } __attribute__((packed));

    def parse_endpoint(self, offset: int) -> Endpoint:
        return Endpoint(
            self.buffer[offset + 2],
            self.buffer[offset + 3],
            self.uint16.unpack_from(self.buffer, offset=offset + 4)[0]
        )

    #  struct USBInterfaceAssociationDescriptor {
    #      uint8_t  bLength,
    #      uint8_t  bDescriptorType,
    #      uint8_t  bFirstInterface,
    #      uint8_t  bInterfaceCount,
    #      uint8_t  bFunctionClass,
    #      uint8_t  bFunctionSubClass,
    #      uint8_t  bFunctionProtocol,
    #      uint8_t  iFunction
    #  } __attribute__((packed));

    def parse_iad(self, offset: int) -> None:
        iad = CompositeFunction(
            self.buffer[offset + 2],
            self.buffer[offset + 3],
            self.buffer[offset + 4],
            self.buffer[offset + 5],
            self.buffer[offset + 6]
        )
        self.configuration.functions.append(iad)

    def peek_desc_length(self, offset: int) -> int:
        return self.buffer[offset]

    def peek_desc_type(self, offset: int) -> int:
        return self.buffer[offset + 1]
