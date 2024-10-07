User Guide
==========

.. currentmodule:: usbx

Installing
----------

usbx can be installed with `pip <https://pip.pypa.io>`_:

.. code-block:: bash

  $ python -m pip install usbx


Enumerating USB devices
-----------------------

:data:`~usb` is a global object and serves as a starting point for most operations.
:meth:`~DeviceRegistry.get_devices` returns the list of currently connected USB devices
(instances of :class:`~Device`).

.. code-block:: python

    from usbx import usb
    for device in usb.get_devices():
        print(device)

.. code-block:: text

    USD device 4295228548, vid=0x2109, pid=0x0813, manufacturer=VIA Labs, Inc., product=USB3.0 Hub, serial=None
    USD device 4295228665, vid=0x0b0e, pid=0x0412, manufacturer=None, product=Jabra SPEAK 410 USB, serial=70398DBDD13Cx011200



Querying information about devices
----------------------------------

For each USB device, descriptive information and details about the interfaces and endpoints are available
through the properties and methods of the :class:`~Device` class:

.. code-block:: python

    from usbx import usb
    for device in usb.get_devices():
        print(f'VID: 0x{device.vid:04x}, PID: 0x{device.pid:04x}')
        print(f'Version: {device.device_version}')
        print(f'Interfaces: {len(device.configuration.interfaces)}')

.. code-block:: text

    VID: 0x2109, PID: 0x0813
    Version: 144.1.1
    Interfaces: 1
    VID: 0x0bda, PID: 0x0412
    Version: 1.7.0
    Interfaces: 1


Enumerating specific device classes
-----------------------------------

Device information can be used to identify USB devices with certain features.
The below code looks for video cameras.

USB video cameras provide an interface with USB class 0x0E and subclass 0x01.
To detect them, one needs to dig into the details of device configuration
(also see :meth:`~Device.configuration` and :class:`~Configuration`).
Each device might have multiple interfaces. So a `for` loop inspects all of them.
The class and subclass codes are found on the currently active alternate setting
(as an interface might have multiple alternate settings).

.. code-block:: python

    CC_VIDEO = 0x0E
    SC_VIDEOCONTROL = 0x01

    def is_video_device(device: Device) -> bool:
        for interface in device.configuration.interfaces:
            alternate = interface.current_alternate
            if alternate.class_code == CC_VIDEO and alternate.subclass_code == SC_VIDEOCONTROL:
                return True
        return False

    for device in usb.find_devices(match = is_video_device):
        print(device)

.. code-block:: text

    USD device 4295228856, vid=0x413c, pid=0xc015, manufacturer=Chicony Tech. Inc., product=Dell Webcam WB7022, serial=3489BB02D84A

:meth:`~DeviceRegistry.find_devices` returns the matching devices. It can take different arguments
to identify the relevant devices. One such argument is ``match``, which takes a function or
lambda expression.


Notifications about connected and disconnected devices
------------------------------------------------------

To be notified when USB device is plugged in or removed from the computer,
callback functions can registered. The functions receive the :class:`~Device` instance
as the only parameter:

.. code-block:: python

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

In the above example ``connected`` and ``disconnected`` are the callback
functions that are registered with :meth:`~DeviceRegistry.on_connected` and
:meth:`~DeviceRegistry.on_disconnected`.


Remembering a particular device
-------------------------------

If multiple devices of the same type are used, the triple of vendor ID, product ID and serial number
can be used to uniquely identify a device. This can be useful to save settings related to a particular device.

.. code-block:: python

    @dataclass
    class DeviceId:
        vid: int
        pid: int
        serial: str

        def matches(self, device: Device) -> bool:
            return (device.vid == self.vid and device.pid == self.pid
              and device.serial == self.serial)

    remembered_device_id = DeviceId(0xcafe, 0xceaf, "35A737883336")

    for device in usb.get_devices():
        if remembered_device_id.matches(device):
            print(f'Remembered device: {device}')
        else:
            print(f'Other device:      {device}')



Using control requests
----------------------

To send a control request, the device is opened first. :meth:`~Device.control_transfer_out` takes
a :class:`~ControlTransfer` instance as its first argument, consisting of request type, recipient, value,
index and data. The purpose of these values depends on the USB device, and device-specific documentation
is usually provided by the device manufacturer. For devices implementing an official USB class,
it is documented in the USB class specification.

In the below example, the test device for testing this library is used.
The possible values and their functionality are documented on GitHub on the
`Loopback device  <https://github.com/manuelbl/JavaDoesUSB/tree/main/test-devices/loopback-stm32#control-requests>`_
page.

.. code-block:: python

    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    transfer = ControlTransfer(RequestType.VENDOR, Recipient.DEVICE, 0x01, 1234, 0)
    test_device.control_transfer_out(transfer)
    test_device.close()

Note that the :class:`~ControlTransfer` instance uses separate fields for request type and recipient
while they are combined in ``bmRequestType`` field in the USB specification.

Control requests are always initiated from the host computer, and the host always waits for
an answer from the device. For *transfer outs*, the response is just an acknowledgement from
the device, typically indicating that the device has executed the command.

For *transfer ins* – executed with :meth:`~Device.control_transfer_in`, the response
consists of data.


Sending interrupt transfers
---------------------------

Interrupt transfers are data packets that are transmitted irregularly,
either from the host to the device or vice versa. Their purpose depends
on the implemented USB class or vendor-specific functionality.

Interrupt transfers are addressed to USB endpoints. Endpoints belong to
a USB interface. Before using interrupt transfers, the USB device must
be opened and the endpoint's interface must be claimed.

.. code-block:: python

    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)
    test_device.transfer_out(3, bytes([0x56, 0x78, 0x9a, 0xbc]))
    test_device.close()

Closing the device will also release the interface.


Receiving interrupt transfers
-----------------------------

Interrupt transfers from the device to the host are used to
communicate irregular events. A host (or rather a thread of the host)
will typically wait for any interrupt transfers.

The below code uses the test device, which will echo all received interrupt
transfers (on IN endpoint 3) twice on the outgoing endpoint (OUT endpoint 3).

.. code-block:: python

    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)

    test_device.transfer_out(3, bytes([0x56, 0x78, 0x9a, 0xbc]))

    data = test_device.transfer_in(3)
    print(f'Received {len(data)} bytes')

    data = test_device.transfer_in(3)
    print(f'Received {len(data)} bytes')

    test_device.close()

Note that *usbx* uses endpoint numbers without a direction bit
to specify endpoints. So the IN and OUT endpoints use the same
number in the above example. Other USB software might use the
addresses 3 and 131 instead.

:meth:`~Device.transfer_in` is a blocking method. If the device
does not send an interrupt transfer, it will wait forever.
It is also possible to specify a timeout duration as the second
parameter. If the timeout is reached, a class:`~TimeoutException`
is raised.


Sending data to bulk endpoints
------------------------------

Bulk endpoints can transmit large amounts of data from and to devices.
They implement a *stream* concept. The chunks of data submitted for
transmission do not directly translate to the transmitted packets as the
operating system can and will join the chunks and divide the resulting
stream into packets as it sees fit.

In the code, sending data to bulk endpoints does not look any different
from sending interrupt transfers (except for the endpoint number).

Whether an endpoint is a bulk or interrupt endpoint is defined in the
device's configuration.

.. code-block:: python

    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)
    test_device.transfer_out(1, "Hello, world!\n".encode())
    test_device.close()


Receiving data from bulk endpoints
----------------------------------

Receiving data from a bulk endpoint is similar to reading data
from a binary file. It is read in chunks. The chunk size cannot be
chosen; :meth:`~Device.transfer_in` will return whatever is
currently available.

The below code uses the test device, which implements a loop
back from IN endpoint 1 to OUT endpoint 2.

Since the division into packets and chunks cannot be controlled,
the code will join multiple chunks if needed.

.. code-block:: python

    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)

    test_device.transfer_out(1, "Hello, world!\n".encode())

    received = bytearray()
    while len(received) < 14:
        chunk = test_device.transfer_in(2)
        received.extend(chunk)

    print(f'Received: {received.decode()}')
    test_device.close()

