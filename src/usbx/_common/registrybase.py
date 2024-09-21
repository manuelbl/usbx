# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from threading import Lock, Condition, Thread
from typing import Optional, Callable

from ..device import Device
from ..exceptions import USBError
from ..registry import DeviceRegistry


def sorted_devices(devices: list[Device]) -> list[Device]:
    return sorted(devices, key=lambda device: device.identifier)


class DeviceRegistryBase(DeviceRegistry):
    """
    Base class for all UsbDeviceRegistry implementations.

    The registry maintains a list of connected USB devices.
    It can notify a client about connected and disconnected USB devices.

    The singleton instance of this class uses a background thread to monitor devices.
    """

    def __init__(self):
        self.connected_callback: Optional[Callable[[Device], None]] = None
        self.disconnected_callback: Optional[Callable[[Device], None]] = None

        self.device_list: Optional[list[Device]] = None
        self.failureReason: Optional[Exception] = None

        self.lock: Lock = Lock()
        self.monitor_condition: Condition = Condition(self.lock)
        self.monitor_thread: Optional[Thread] = None

    def find_devices(self, match: Callable[[Device], bool] = None, **kwargs) -> list[Device]:

        def matches(device: Device) -> bool:
            for key, val in kwargs.items():
                if getattr(device, key) != val:
                    return False
            if match is not None:
                return match(device)
            return True

        return list(filter(matches, self.get_devices()))

    def find_device(self, match: Callable[[Device], bool] = None, **kwargs) -> Optional[Device]:
        devices = self.find_devices(match, **kwargs)
        return devices[0] if len(devices) >= 1 else None

    def on_connected(self, callback: Optional[Callable[[Device], None]]) -> None:
        self.connected_callback = callback

    def on_disconnected(self, callback: Optional[Callable[[Device], None]]) -> None:
        self.disconnected_callback = callback

    def get_devices(self) -> list[Device]:
        """
        Gets the list of connected USB devices.

        Starts the background monitor if needed and waits for the initial enumeration.
        :return: list of :class:`Device` objects
        """
        if self.device_list is None:
            self.start_monitor()
        return self.device_list

    def monitor_devices(self) -> None:
        # to be implemented by subclasses
        pass

    def start_monitor(self) -> None:
        """
        Starts the background monitor thread and waits until the initial enumeration is complete.

        :exception USBError: Raised if the initial enumeration fails.
        """
        self.failureReason = None
        self.device_list = None

        self.monitor_thread = Thread(target=self.monitor_devices, daemon=True)
        self.monitor_thread.start()

        with self.monitor_condition:
            self.monitor_condition.wait_for(lambda: self.device_list is not None or self.failureReason is not None)

        if self.failureReason is not None:
            raise USBError('initial device enumeration has failed') from self.failureReason

    def notify_enumeration_complete(self, devices: list[Device]) -> None:
        """
        Sets the initial list of devices and notifies other threads that the initial enumeration is complete.
        :param devices: the list of discovered devices.
        """
        with self.monitor_condition:
            self.device_list = sorted_devices(devices)
            self.monitor_condition.notify_all()

    def notify_enumeration_failed(self, exception: Exception) -> None:
        """
        Notifies other thread that the initial device enumeration has failed.
        :param exception: Exception raised by failure.
        """
        with self.monitor_condition:
            self.failureReason = exception
            self.monitor_condition.notify_all()

    def find_device_by_id(self, identifier: str) -> Optional[Device]:
        return next((device for device in self.device_list if device.identifier == identifier), None)

    def add_device(self, device: Device) -> None:
        """
        Adds a USB device to the list of connected devices.

        Additionally, calls the registered ``on_connected`` callback functions.
        :param device: The newly connected USB device.
        """
        with self.lock:
            self.device_list = sorted_devices(self.device_list + [device])
        on_connected = self.connected_callback
        if on_connected is not None:
            on_connected(device)

    def close_and_remove_device(self, identifier: str) -> None:
        """
        Removes a disconnected USB device from the list of connected devices.

        Additionally, calls the registered ``on_disconnected`` callback functions.
        :param identifier: Identifier of device to remove.
        """
        with self.lock:
            device = self.find_device_by_id(identifier)
            if device is None:
                return
            device.close()
            device.is_connected = False
            self.device_list.remove(device)

        on_disconnected = self.disconnected_callback
        if on_disconnected is not None:
            on_disconnected(device)
