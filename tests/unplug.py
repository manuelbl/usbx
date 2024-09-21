# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import time
from random import Random
from threading import Thread, current_thread
from typing import Callable

from tests.deviceconfig import get_config, TestDeviceConfig
from usbx import usb, Device, USBError


class Work(object):
    start_time: float = 0
    expected_work_per_sec: int = 0
    actual_work: int = 0
    finish_time: float = 0


class PRNG(object):
    def __init__(self, seed: int):
        self._random: Random = Random()
        self._random.seed(seed)
        self._position: int = 0

    def get_bytes(self, num_bytes: int) -> bytes:
        self._position += num_bytes
        return self._random.randbytes(num_bytes)

    def validate_bytes(self, data: bytes) -> None:
        expected: bytes = self._random.randbytes(len(data))
        assert data == expected


class DeviceWorker(object):
    def __init__(self, device: Device, config: TestDeviceConfig):
        self.device: Device = device
        self.config: TestDeviceConfig = config
        self.work_tracking: dict[Thread, Work] = {}
        self.seed: int = int(time.time())
        self.disconnect_time: float = 0

    def start(self) -> None:
        print('Device connected')
        self.device.open()
        self.device.claim_interface(self.config.interface_number)

        # start loopback sender and receiver
        self.start_thread(self.send_loopback_data)
        self.start_thread(self.receive_loopback_data)

        if not self.config.is_composite:
            self.start_thread(self.send_echo)
            self.start_thread(self.receive_echo)

    def send_loopback_data(self) -> None:
        self.log_start('sending loopback data', 300_000)
        prng = PRNG(self.seed)

        while True:
            data = prng.get_bytes(5000)
            self.device.transfer_out(self.config.endpoint_loopback_out, data, 0.2)
            self.log_work(len(data))

    def receive_loopback_data(self) -> None:
        self.log_start('receiving loopback data', 300_000)
        prng = PRNG(self.seed)

        while True:
            data = self.device.transfer_in(self.config.endpoint_loopback_in)
            prng.validate_bytes(data)
            self.log_work(len(data))

    def send_echo(self) -> None:
        self.log_start('sending echoes', 7)
        data = bytes([0x03, 0x45, 0x73, 0xb3, 0x9f, 0x3f, 0x00, 0x6a])
        while True:
            self.device.transfer_out(self.config.endpoint_echo_out, data)
            self.log_work(1)
            time.sleep(0.1)

    def receive_echo(self) -> None:
        self.log_start('receiving echoes', 14)
        while True:
            self.device.transfer_in(self.config.endpoint_echo_in)
            self.log_work(1)

    def start_thread(self, action: Callable[[], None]) -> None:
        thread = Thread(target=self.run_action, args=(action,))
        work = Work()
        self.work_tracking[thread] = work
        thread.start()

    def run_action(self, action: Callable[[], None]) -> None:
        try:
            action()
        except USBError:
            self.log_finish()

    def log_start(self, operation: str, expected_work_per_sec: int) -> None:
        current_thread().name = operation
        work = self.work_tracking[current_thread()]
        work.start_time = time.time()
        work.expected_work_per_sec = expected_work_per_sec

    def log_work(self, amount: int) -> None:
        work = self.work_tracking[current_thread()]
        work.actual_work += amount

    def log_finish(self) -> None:
        work = self.work_tracking[current_thread()]
        work.finish_time = time.time()

    def set_disconnect_time(self) -> None:
        self.disconnect_time = time.time()

    def join(self) -> None:
        for thread in self.work_tracking.keys():
            thread.join(5)
            if thread.is_alive():
                print(f'Thread {thread.name} failed to join within 5s')

        self.device.close()

        # check achieved work
        for thread, work in self.work_tracking.items():
            expected_work = work.expected_work_per_sec * (work.finish_time - work.start_time)
            if work.actual_work < expected_work:
                print(f'Thread {thread.name} achieved insufficient work. Expected: {expected_work:.0f}, achieved:{work.actual_work:.0f}')

        # check that the threads haven't finished early
        for thread, work in self.work_tracking.items():
            duration = abs(work.finish_time - self.disconnect_time)
            if duration > 0.5:
                print(f'Thread {thread.name} quit early and has likely crashed')

        print('Device disconnected')


active_devices: dict[Device, DeviceWorker] = {}


def on_connected_device(device: Device) -> None:
    config = get_config(device)
    if config is None:
        return

    worker = DeviceWorker(device, config)
    active_devices[device] = worker
    worker.start()


def on_disconnected_device(device: Device) -> None:
    config = get_config(device)
    if config is None:
        return

    worker = active_devices.pop(device)
    worker.set_disconnect_time()
    worker.join()

    # check that device can no longer be opened
    Thread(target=check_disconnected, args=(device,)).start()

def check_disconnected(device: Device) -> None:
    time.sleep(2)
    try:
        device.open()
        print('Error: device should not be openable after disconnect')
    except USBError as err:
        if 'connected' not in str(err):
            print(f'Unexpected error: {err}')


if __name__ == '__main__':
    print('Plug and unplug test device multiple times')
    print('Hit ENTER to exit.')

    usb.on_connected(on_connected_device)
    usb.on_disconnected(on_disconnected_device)
    for dev in usb.get_devices():
        on_connected_device(dev)

    input()
