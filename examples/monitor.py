# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from usbx import usb, Device


if __name__ == '__main__':
    def connected(device: Device) -> None:
        print(f'Connected:    {device}')

    def disconnected(device: Device) -> None:
        print(f'Disconnected: {device}')

    usb.on_connected(connected)
    usb.on_disconnected(disconnected)

    print("Press Enter to exit...\n")
    for dev in usb.find_devices():
        print(f'Present:      {dev}')
    input()
