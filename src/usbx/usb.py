# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import platform

from .registry import DeviceRegistry

# Import the device registry suitable for the current platform
_os = platform.system()
_arch = platform.machine()
if _os == 'Darwin' and _arch in ['arm64', 'x86_64']:
    from ._macos.macosregistry import MacosDeviceRegistry as NativeDeviceRegistry
elif _os == 'Linux' and _arch in ['x86_64', 'aarch64']:
    from ._linux.linuxregistry import LinuxDeviceRegistry as NativeDeviceRegistry
elif _os == 'Windows' and _arch in ['AMD64', 'ARM64']:
    from ._windows.winregistry import WindowsDeviceRegistry as NativeDeviceRegistry
else:
    raise NotImplementedError(f'The library "usbx" is not supported on platform {_os}/{_arch}')

usb: DeviceRegistry = NativeDeviceRegistry()
"""
Global device registry.

This object is the starting point for accessing the connected devices
and configuring notifications about connected and disconnected devices.
"""
