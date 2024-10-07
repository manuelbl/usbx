Platform-specific Considerations
================================

macOS
-----

No special considerations apply. Using this library, a Python application can connect to any USB device
and claim any interface that isn't claimed by an operating system driver or another application.
Standard operation system drivers can be unloaded if the application is run with root privileges.

This library runs both on Macs with Apple Silicon and Intel processors.


Linux
-----

`libudev` is used to discover and monitor USB devices. It is closely tied to `systemd`.
So the library only runs on Linux distributions with `systemd` and related libraries.
This is fulfilled by the majority of Linux distributions suitable for desktop computing
(as opposed to distributions optimized for containers).
It runs on both x86-64 (Intel, AMD) and ARM64 processors.

Using this library, a Python application can connect to any USB device and claim any
interfaces that isn't claimed by an operating system driver or another application.
Standard operation system drivers can be unloaded (without the need for root privileges).

Most Linux distributions set up user accounts without permissions to access USB devices.
The `udev` system daemon is responsible for assigning permissions to USB devices
when they are connected.

To configure it to assign specific permissions or ownership,
create a file called ``/etc/udev/rules.d/80-usbx-udev.rules`` with the below content:

.. code-block:: text

    SUBSYSTEM=="usb", ATTRS{idVendor}=="cafe", MODE="0666"

Then disconnect and reconnect the USB device.
The above files adds a rule to assign permission mode 0666 to all USB devices
with vendor ID `0xCAFE`. This unregistered vendor ID is used by the test devices.
Similar rules can be configured for other vendor or product IDs, or for all USB
devices. The filename can be chosen freely but must have the same file extension
and go into that particular directory.

Without the `udev` rule, it is still possible to enumerate and query all USB devices.


Windows
-------

The Windows driver model is rather rigid. It's not possible to open any USB device unless
it uses the `WinUSB` driver. This even applies to devices with no installed driver.
Enumerating and querying USB devices is possible independent of the driver.

USB devices can implement special control requests to instruct Windows to automatically
install the `WinUSB` driver (search the internet for `WCID` or `Microsoft OS Compatibility Descriptors`).
The `WinUSB` driver can also be manually installed or replaced using a software called `Zadig`.

The test devices implement the required control requests. So the driver is installed automatically.

This library runs on both Windows for x86-64 (Intel, AMD) and Windows for ARM (ARM64).
