# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from typing import Optional

from .enums import TransferDirection
from .version import Version
from .configuration import Interface, Endpoint, Configuration
from .controltransfer import ControlTransfer


class Device:
    """
    USB device.

    This class provides the functions to query details about a USB device
    and to communicate with it.

    In order to make control requests and transfer data, the device must be
    opened and an interface must be claimed. In the open state, the current
    process has exclusive access to the claimed interfaces.

    Information about the device is always available, without opening
    the device and even after it has been unplugged.

    Instances of this class are created by the global device registry
    when a USB device is plugged in and when the registry starts. They are
    active until the USB device is unplugged. Thereafter, information can still
    be queried but all communication related functions no longer work.
    """

    def __init__(self, identifier: str):
        self.identifier: str = identifier
        """
        Unique identifier for the USB device.
        
        Valid as long as the device is connected.
        """

        self.vid: int = 0
        """USB vendor ID."""

        self.pid: int = 0
        """USB product ID."""

        self.manufacturer: Optional[str] = None
        """Product manufacturer."""

        self.product: Optional[str] = None
        """Product name."""

        self.serial: Optional[str] = None
        """Serial number."""

        self.device_descriptor: bytes = bytes()
        """USB device descriptor (raw bytes)."""

        self.configuration_descriptor: bytes = bytes()
        """USB configuration descriptor (raw bytes)."""

        self.class_code: int = 0
        """Device class code."""

        self.subclass_code: int = 0
        """Device subclass code."""

        self.protocol_code: int = 0
        """Device protocol code."""

        self.device_version: Version = Version(0)
        """Device version."""

        self.usb_version: Version = Version(0)
        """Implemented USB version."""

        self.max_packet_size: int = 0
        """Maximum packet size for control endpoint 0."""

        self.is_connected: bool = True
        """Boolean indicating if the device is connected."""

        self.is_open: bool = False
        """Boolean indicating if the device is open."""

        self.configuration_value: int = 0
        """Active configuration value."""

        self.configuration: Configuration = Configuration()
        """Information about USB interfaces, endpoints and composite functions."""

    def open(self) -> None:
        """
        Open the USB device for communication.

        :raises USBError: If the USB device is already open or if it cannot be opened.
        """
        pass

    def close(self) -> None:
        """
        Close the USB device.

        If the USB device is already closed, this method does not do anything.
        """
        pass

    def get_interface(self, number: int) -> Optional[Interface]:
        """
        Get :class:`Interface` instance for interface with number ``number``.
        :param number: Interface number.
        :return: :class:`Interface` instance, or ``None`` if no interface with the given number exists.
        """
        pass

    def get_endpoint(self, number: int, direction: TransferDirection) -> Optional[Endpoint]:
        """
        Get :class:`Endpoint` instance with number ``number`` and direction ``direction``.

        This method considers the endpoints of all interfaces, whether claimed or not.
        For each interface, the endpoints of the currently active alternate setting are considered..
        Control endpoint 0 is excluded.

        :param number: Endpoint number (between 0 and 127).
        :param direction: Endpoint transfer direction.
        :return: :class:`Endpoint` instance, or ``None`` if no matching endpoint exists.
        """
        pass

    def claim_interface(self, number: int) -> None:
        """
        Claim a USB interface for exclusive use.

        Except for control endpoint 0, an interface must be claimed before communication
        with one of its endpoints is possible.

        :param number: Interface number.
        """
        pass

    def release_interface(self, number: int) -> None:
        """
        Release the USB interface with number ``number``.

        :param number: Interface number.
        """
        pass

    def select_alternate(self, interface_number: int, alternate_number: int) -> None:
        """
        Select the alternate setting for the specified interface and make it the active setting.

        The device must be open and the interface must have been claimed.

        :param interface_number: Interface number.
        :param alternate_number: Alternate setting number.
        """
        pass

    def control_transfer_in(self, transfer: ControlTransfer, length: int) -> bytes:
        """
        Request data from the control endpoint.

        The control transfer request is sent to endpoint 0. The transfer is
        expected to have a `Data In` stage.

        Requests with an interface or an endpoint as the recipient are
        expected to have the interface number or endpoint address, respectively, in
        the lower byte of ``index``. The addressed interface or addressed
        endpoint's interface must have been claimed.

        This method blocks until the devices has responded or an error has
        occurred.

        :param transfer: Control transfer request.
        :param length: Maximum length of expected data.
        :return: Received data.
        """
        pass

    def control_transfer_out(self, transfer: ControlTransfer, data: Optional[bytes] = None) -> None:
        """
        Execute a control transfer request and optionally send data.

        The control transfer request and the provided data are sent to
        endpoint 0. The transfer is expected to either have no data stage or
        a `Data Out` stage.

        Requests with an interface or an endpoint as the recipient are
        expected to have the interface number or endpoint address, respectively, in
        the lower byte of ``index``. The addressed interface or addressed
        endpoint's interface must have been claimed.

        This method blocks until the devices has responded or an error has
        occurred.

        :param transfer: Control transfer request.
        :param data: Data to send, or ``None`` for no data stage.
        """
        pass

    def transfer_in(self, endpoint_number: int, timeout: Optional[float] = None) -> bytes:
        """
        Receive data from the specified endpoint of this device.

        This method blocks until at least one byte has been received, the timeout
        (if specified) has expired, or an error has occurred.

        The returned bytes are the payload of the transfer. It can have a length
        of 0 if the device sends zero-length packets to indicate the end of a
        data unit.

        This method can receive data from bulk and interrupt endpoints only.
        The interface the endpoint belongs to must have been claimed.

        :param endpoint_number: Endpoint number (between 1 and 127).
        :param timeout: Optional timeout, in seconds.
        :return: Received data.
        :raises TransferTimeoutError: If the timeout occurred.
        :raises StallError: If the device stalled.
        """
        pass

    def transfer_out(self, endpoint_number: int, data: bytes, timeout: Optional[float] = None) -> None:
        """
        Send data to the specified endpoint of this device.

        This method blocks until the data has been sent, the timeout
        (if specified) has expired, or an error has occurred.

        This method can receive data from bulk and interrupt endpoints only.
        The interface the endpoint belongs to must have been claimed.

        If the sent data's length is a multiple of the packet size, it is often
        required to send an additional zero-length packet (ZLP) for the device
        to actually process the data. This method will not do it automatically.

        :param endpoint_number: Endpoint number (between 1 and 127).
        :param data: Data to send.
        :param timeout: Optional timeout, in seconds.
        :raises TransferTimeoutError: If the timeout occurred.
        :raises StallError: If the device stalled.
        """
        pass

    def clear_halt(self, number: int, direction: TransferDirection) -> None:
        """
        Clear an endpoint's halt condition.

        An endpoint is halted (aka as stalled) if an error occurs in the communication.
        Before the communication can resume, the halt condition must be cleared.
        Two endpoints with the same number but a different transfer direction have separate
        halt conditions.

        A halt condition of control endpoint 0 is automatically cleared.

        :param number: Endpoint number.
        :param direction: Endpoint direction.
        """
        pass

    def abort_transfers(self, number: int, direction: TransferDirection) -> None:
        """
        Abort all transfers on an endpoint.

        This method is mainly useful to unblock a thread waiting for a transfer.
        It will always be called from a different thread than the one making the transfer.

        This operation is not valid on control endpoint 0.

        :param number: Endpoint number.
        :param direction: Endpoint direction.
        """
        pass


    def detach_standard_drivers(self) -> None:
        """
        Detach the standard operating-system drivers from this device.

        By detaching the standard drivers, the operating system releases the exclusive access to the device
        and/or some or all of the device's interfaces. This allows the application to open the device and claim
        interfaces. It is relevant for device and interfaces implementing standard USB classes, such as HID, CDC
        and mass storage.

        This method should be called before the device is opened. After the device has been closed,
        ``attach_standard_drivers`` should be called to restore the previous state.

        On macOS, all device drivers are immediately detached from the device. To execute it, the application must
        be run as *root*. Without *root* privileges, the method does nothing.

        On Linux, this method changes the behavior of ``claim_interface`` and ``release_interface`` for this device.
        The standard drivers will be detached interface by interface when the interface is claimed, and they will be
        reattached interface by interface when the interface is released.

        On Windows, this method does nothing. It is not possible to temporarily change the drivers.
        """
        pass

    def attach_standard_drivers(self) -> None:
        """
        Reattach the standard operating-system drivers to this device.

        By attaching the standard drivers, the operating system claims the device and/or its interfaces if they
        implement standard USB classes, such as HID, CDC and mass storage. It is used to restore the state after
        calling ``detach_standard_drivers``.

        On macOS, the application must be run as *root*. Without *root* privileges, the method does nothing.

        On Linux, this method does nothing as the drivers are automatically reattached when the interface is released,
        or at the latest when the device is closed.

        On Windows, this method does nothing. It is not possible to temporarily change the drivers.

        :return:
        """
