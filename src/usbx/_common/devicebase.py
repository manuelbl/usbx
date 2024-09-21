# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from threading import Lock
from typing import Optional

from .._common.confparser import USBConfigurationParser
from ..configuration import Interface, Endpoint
from ..device import Device
from ..enums import TransferDirection, Recipient, TransferType
from ..exceptions import USBError
from ..version import Version
from ..controltransfer import ControlTransfer


class DeviceBase(Device):
    """
    Base implementation of ``Device``.
    """

    def __init__(self, identifier: str):
        super().__init__(identifier)
        self._device_lock = Lock()  # Lock used when manipulating the device

    def __str__(self) -> str:
        return (f'USD device {self.identifier}, vid=0x{self.vid:04x}, pid=0x{self.pid:04x}, '
                f'manufacturer={self.manufacturer}, product={self.product}, serial={self.serial}')

    def get_interface(self, number: int) -> Optional[Interface]:
        for intf in self.configuration.interfaces:
            if intf.number == number:
                return intf
        return None

    def get_endpoint_and_interface(self, number: int, direction: TransferDirection
                                   ) -> Optional[tuple[Endpoint, Interface]]:
        """
        Gets the endpoint and interface descriptor of the specified endpoint.
        :param number: Endpoint number
        :param direction: Endpoint direction
        :return: Tuple of endpoint and interface descriptor, or ``None`` if the endpoint does not exist
        """
        for intf in self.configuration.interfaces:
            for endpoint in intf.current_alternate.endpoints:
                if endpoint.number == number and endpoint.direction == direction:
                    return endpoint, intf
        return None

    def get_endpoint(self, number: int, direction: TransferDirection) -> Optional[Endpoint]:
        endpoint, _ = self.get_endpoint_and_interface(number, direction) or (None, None)
        return endpoint

    def get_and_check_interface(self, number: int, expect_claimed: bool) -> Interface:
        """
        Checks that the specified interface exists and has the expected claimed state.
        Returns the interface descriptor.
        :param number: interface number
        :param expect_claimed: expected claimed state of interface
        :return: interface descriptor
        """
        intf = self.get_interface(number)
        if intf is None:
            raise USBError(f'Interface {number} does not exist')
        if expect_claimed and not intf.is_claimed:
            raise USBError(f'Interface {number} must be claimed first')
        elif not expect_claimed and intf.is_claimed:
            raise USBError(f'Interface {number} has already been claimed')
        return intf

    def check_alternate_interface(self, interface_number: int, alternate_number: int) -> None:
        """
        Checks tha the device is open, the interface is claimed and the alternate interface
        number is valid for the interface.
        :param interface_number: interface number.
        :param alternate_number: alternate setting number.
        """
        self.check_is_open()
        intf = self.get_and_check_interface(interface_number, True)
        alternate = intf.get_alternate(alternate_number)
        if alternate is None:
            raise USBError(f'Interface {interface_number} has no alternate setting {alternate_number}')

    def set_descriptors(self, device_desc: bytes, config_desc: bytes) -> None:
        self.device_descriptor = device_desc
        self.usb_version = Version(device_desc[2] + 256 * device_desc[3])
        self.class_code = device_desc[4]
        self.subclass_code = device_desc[5]
        self.protocol_code = device_desc[6]
        self.max_packet_size = device_desc[7]
        self.device_version = Version(device_desc[12] + 256 * device_desc[13])

        self.configuration_descriptor = config_desc
        self.configuration = USBConfigurationParser.parse_bytes(config_desc)
        self.configuration_value = self.configuration.configuration_value

    def check_is_open(self) -> None:
        if not self.is_open:
            raise USBError('Device must be opened first')

    def check_is_closed_and_connected(self) -> None:
        if self.is_open:
            raise USBError('Device cannot be open for this operation')
        if not self.is_connected:
            raise USBError('Device is no longer connected')

    def check_control_transfer(self, transfer: ControlTransfer, direction: TransferDirection) -> None:
        """
        Checks that the device is open. If an interface or endpoint has been specified,
        also checks that the index specifies a valid recipient and that the relevant
        interface has been claimed.

        :param transfer: control transfer
        :param direction: control transfer direction
        """
        self.check_is_open()
        if transfer.recipient == Recipient.INTERFACE:
            self.get_and_check_interface(transfer.index & 0xff, True)
        elif transfer.recipient == Recipient.ENDPOINT:
            address = transfer.index & 0xff
            _, interface = self.get_endpoint_and_interface(Endpoint.get_number(address),
                                                           Endpoint.get_direction(address)) or (None, None)
            if interface is None:
                raise USBError(f'Endpoint {transfer.index & 0xff:02x} (lower byte of \'index\') does not exist')
            self.get_and_check_interface(interface.number, True)

    def get_and_check_endpoint_and_interface(self, number: int, direction: TransferDirection
                                             ) -> tuple[Endpoint, Interface]:
        """
        Checks that the specified endpoint exists and that the associated interface has been claimed.
        Additionally, it is checked that the endpoint has transfer type *bulk* or *interrupt*.
        :param number: Endpoint number
        :param direction: Endpoint direction
        :return: Tuple of endpoint and interface descriptor
        """
        if number == 0:
            raise USBError('Control endpoint 0 supports control transfers only')
        endpoint, interface = self.get_endpoint_and_interface(number, direction) or (None, None)
        if endpoint is None:
            raise USBError(f'Device has no {direction.name} endpoint {number}')
        if endpoint.transfer_type not in [TransferType.BULK, TransferType.INTERRUPT]:
            raise USBError(f'Transfer requires BULK or INTERRUPT endpoint'
                               f' ({direction.name} endpoint {number} has type {endpoint.transfer_type.name})')
        if not interface.is_claimed:
            raise USBError(f'Interface {interface.number} must be claimed for transfer')
        return endpoint, interface

    def set_claimed(self, interface_number: int, claimed: bool) -> None:
        intf = self.get_interface(interface_number)
        intf._is_claimed = claimed

    def set_current_alternate(self, interface_number: int, alternate_number: int) -> None:
        intf = self.get_interface(interface_number)
        alt = intf.get_alternate(alternate_number)
        intf._current_alternate = alt

    def detach_standard_drivers(self) -> None:
        self.check_is_closed_and_connected()

    def attach_standard_drivers(self) -> None:
        self.check_is_closed_and_connected()
