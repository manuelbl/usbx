# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from typing import Optional, Callable

from .device import Device


class DeviceRegistry:
    """
    USB device registry.

    The registry maintains a list of connected USB devices.
    It can notify a client about connected and disconnected USB devices.

    All methods consistently return the same :class:`Device` instance for the
    same physical USB device as long as it is plugged in.
    """

    def get_devices(self) -> list[Device]:
        """
        Get the list of currently connected USB devices.

        :return: list of :class:`Device` objects
        """
        pass

    def find_devices(self, match: Callable[[Device], bool] = None, **kwargs) -> list[Device]:
        """
        Find USB devices matching the specified criteria.

        Criteria can be specified as keyword arguments. They match the properties
        of the :class:`Device` class, i.e. `vid`, `pid`, `manufacturer`, `product`, `serial`::

            find_devices(vid=0x1234, product='Webcam ABC')

        Alternatively, a matching function taking a :class:`Device` object as the single parameter can be specified::

            find_devices(lambda device: device.vid == 0x1234)

        If both criteria and a matching function are specified, both must match.

        :param match: Lambda function testing if a device matches.
        :param kwargs: Keywords arguments specifying matching criteria as property name/value pairs.
        :return: List of matching :class:`Device` objects.
        """
        pass

    def find_device(self, match: Callable[[Device], bool] = None, **kwargs) -> Optional[Device]:
        """
        Find the first USB device matching the specified criteria.

        Criteria can be specified as keyword arguments. They match the properties
        of the :class:`Device` class, i.e. `vid`, `pid`, `manufacturer`, `product`, `serial`::

            find_device(vid=0x1234, product='Webcam ABC')

        Alternatively, a matching function taking a :class:`Device` object as the single parameter can be specified::

            find_device(lambda device: device.vid == 0x1234)

        If both criteria and a matching function are specified, both must match.

        :param match: Lambda function testing if a device matches.
        :param kwargs: Keywords arguments specifying matching criteria as property name/value pairs.
        :return: Matching :class:`Device` object or ``None``.
        """
        pass

    def on_connected(self, callback: Optional[Callable[[Device], None]]) -> None:
        """
        Register a function to be called when a USB device is connected.

        The function's only parameter will receive the :class:`Device` instance
        that has been connected.

        The callback function will be called from a background thread. It should not execute
        long-running operations as it blocks further notifications.

        :param callback: Function to be called, or ``None`` to cancel callbacks.
        """
        pass

    def on_disconnected(self, callback: Optional[Callable[[Device], None]]) -> None:
        """
        Register a function to be called when a USB device has been disconnected.

        The function's only parameter will receive the :class:`Device` instance
        that has been disconnected. Even though the device has been connected, the
        instance retains the descriptive information about the device.

        The callback function will be called from a background thread. It should not execute
        long-running operations as it blocks further notifications.

        :param callback: Function to be called, or ``None`` to cancel callbacks.
        """
        pass
