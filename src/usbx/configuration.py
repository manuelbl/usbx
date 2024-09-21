# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from typing import Optional

from .enums import TransferType, TransferDirection


class Endpoint(object):
    """
    USB endpoint information.

    The information originates from the configuration descriptor provided by the USB device.
    """

    def __init__(self, address: int, attributes: int, max_packet_size: int):
        self.number: int = Endpoint.get_number(address)
        """
        Endpoint number (without direction bit).
        
        The endpoint number is between 0 and 127.
        Endpoint 0 is the control endpoint.
        """

        self.direction: TransferDirection = Endpoint.get_direction(address)
        """Transfer direction."""

        self.transfer_type: TransferType = TransferType.from_attributes(attributes)
        """Transfer type."""

        self.max_packet_size: int = max_packet_size
        """Maximum packet size (in bytes)."""

    @classmethod
    def get_number(cls, address: int) -> int:
        """
        Get the endpoint number from an endpoint address.

        In the USB specification and in the interface descriptor, the endpoint
        address is usually named ``bEndpointAddress``.

        :param address: Endpoint address (between 0 and 255).
        :return: Endpoint number (between 0 and 127).
        """
        return address & 0x7f

    @classmethod
    def get_direction(cls, address: int) -> TransferDirection:
        """
        Get the endpoint direction from an endpoint address.

        In the USB specification and in the interface descriptor, the endpoint
        address is usually named ``bEndpointAddress``.

        :param address: Endpoint address (between 0 and 255).
        :return: Transfer direction.
        """
        return TransferDirection.OUT if (address & 0x80) == 0 else TransferDirection.IN

    @classmethod
    def get_address(cls, number: int, direction: TransferDirection) -> int:
        """
        Get the endpoint address from an endpoint number and direction.

        :param number: Endpoint number (between 0 and 127).
        :param direction: Endpoint direction.
        :return: Endpoint address.
        """
        return number if direction == TransferDirection.OUT else number | 0x80


class AlternateInterface(object):
    """
    USB alternate interface setting information.

    USB interface can have multiple settings. Settings enable and disable endpoints
    and configure their communication parameters such as interval length.

    The information originates from the configuration descriptor provided by the USB device.
    """

    def __init__(self, number: int, class_code: int, subclass_code: int, protocol_code: int):
        self.number: int = number
        """Alternate setting number (``bAlternateSetting`` in USB interface descriptor)."""

        self.class_code: int = class_code
        """Interface class code (``bInterfaceClass`` in USB interface descriptor)."""

        self.subclass_code: int = subclass_code
        """Interface sub class code (``bInterfaceSubClass`` in USB interface descriptor)."""

        self.protocol_code: int = protocol_code
        """Interface protocol code (``bInterfaceProtocol`` in USB interface descriptor)."""

        self.endpoints: list[Endpoint] = []
        """USB endpoints (excluding control endpoint)."""


class Interface(object):
    """
    USB interface information.

    The information originates from the configuration descriptor provided by the USB device.
    """

    def __init__(self, number: int, alternates: list[AlternateInterface]):
        self.number: int = number
        """USB interface number (``bInterfaceNumber`` of USB interface descriptor)."""

        self.alternates: list[AlternateInterface] = alternates
        """USB alternate interfaces."""

        self._current_alternate: AlternateInterface = alternates[0]

        self._is_claimed: bool = False

    def get_alternate(self, number: int) -> Optional[AlternateInterface]:
        """
        Get the USB alternate interface settings with number ``number``.

        :param number: USB alternate setting number.
        :return: USB alternate interface, or ``None`` if there is no alternate setting with the given number.
        """
        return next((alternate for alternate in self.alternates if alternate.number == number), None)

    @property
    def current_alternate(self) -> AlternateInterface:
        """
        Currently active alternate interface.

        This property is not information from the configuration descriptor
        but rather represents the current state of the device.
        """
        return self._current_alternate

    @property
    def is_claimed(self) -> bool:
        """
        Boolean indicating if the interface is claimed.

        Before communication on endpoints is possible, the interface must
        be claimed for exclusive use by the application.

        This property is not information from the configuration descriptor
        but rather represents the current state of the device.
        """
        return self._is_claimed


class CompositeFunction(object):
    """
    USB composite function information.

    A composite USB device can have multiple functions, e.g. a mass
    storage function and a virtual serial port function. Each function
    will appear as a separate device in Window.

    A function consists of one or more interfaces. Functions with
    multiple interfaces have consecutive interface numbers. The
    interfaces after the first one are called associated interfaces.

    If a function consists of multiple interfaces, the USB configuration
    description will contain an IAD (Interface Association Descriptor)
    to specify which interfaces belong to the function.

    This information originates from the configuration descriptor provided by the USB device.
    """

    def __init__(self, first_intf_number: int, interface_count: int, class_code: int, subclass_code: int,
                 protocol_code: int):

        self.first_intf_number: int = first_intf_number
        """Interface number of first interface belonging to this function."""

        self.interface_count: int = interface_count
        """Number of interfaces belonging to this function."""

        self.class_code: int = class_code
        """IAD class code (``bInterfaceClass`` in USB interface descriptor)."""

        self.subclass_code: int = subclass_code
        """IAD sub class code (``bInterfaceSubClass`` in USB interface descriptor)."""

        self.protocol_code: int = protocol_code
        """IAD protocol code (``bInterfaceProtocol`` in USB interface descriptor)."""


class Configuration(object):
    """
    USB device configuration information.

    This object is the root object for information originating from the
    configuration descriptor provided by the USB device.
    """

    def __init__(self):
        self.configuration_value: int = 0
        """Value/number of this configuration (``bConfigurationValue`` of USB configuration descriptor)."""

        self.attributes: int = 0
        """Configuration attributes (``bmAttributes`` of USB configuration descriptor)."""

        self.max_power: int = 0
        """Maximum Power Consumption in 2mA units (``bMaxPower`` of USB configuration descriptor)."""

        self.interfaces: list[Interface] = []
        """USB interfaces."""

        self.functions: list[CompositeFunction] = []
        """USB composite functions."""

    def get_interface(self, number: int) -> Optional[Interface]:
        """
        Get the USB interface with number ``number``.

        :param number: USB interface number.
        :return: USB interface, or ``None`` if there is no interface with the given number.
        """
        return next((interface for interface in self.interfaces if interface.number == number), None)

    def get_function(self, number: int) -> Optional[CompositeFunction]:
        """
        Find the USB composite function the interface with number ``number`` belongs to.

        :param number: USB interface number.
        :return: USB composite function, or ``None`` if there is no function for the given interface number.
        """
        for function in self.functions:
            if function.first_intf_number <= number < function.first_intf_number + function.interface_count:
                return function
        return None
