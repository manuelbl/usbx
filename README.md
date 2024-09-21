<h1 align="center">

![usbx](https://github.com/manuelbl/usbx/raw/main/docs/_static/usbx-github.svg)

</h1>


**usbx** is a modern, powerful and user-friendly Python library for working with USB devices.
It provides many useful features:

- Querying information about connected devices
- Communication with USB devices
- Notification when devices are connected and disconnected
- Single API for Windows, Linux and macOS
- Good documentation
- Thread-safe
- No need to install further software like *libusb*

**usbx** is easy to use:

```pycon
>>> from usbx import usb
>>> for device in usb.get_devices():
...     print(device)
...
USD device 4295171929, vid=0x1a40, pid=0x0801, manufacturer=None, product=USB 2.0 Hub, serial=None
USD device 4295171974, vid=0x0b0e, pid=0x0412, manufacturer=None, product=Jabra SPEAK 410 USB, serial=783F92B9DD3Cx011200
```


## Installing

**usbx** can be installed with [pip](https://pip.pypa.io):

```shell
python -m pip install usbx
```



## Usage

The [User Guide](https://usbx.readthedocs.io/en/stable/user-guide.html) will get you started with the library.
Also read [Platform-specific Considerations](https://usbx.readthedocs.io/en/stable/platform-specific.html)
as some operating systems might need extra steps to work with USB devices.



The [API Reference](https://usbx.readthedocs.io/en/stable/reference/index.html) documentation provides API-level documentation.


## License

**usbx** is made available under the MIT License. For more details, see [The MIT License](https://opensource.org/licenses/MIT>).


## Contributing

This is an open-source project that happily accepts contributions.
Please see [Contributing](https://usbx.readthedocs.io/en/stable/contributing.html) for details.


## System Requirements

- Python 3.9 or higher
- 64-bit application
- Windows (x86-64 or ARM), Linux (x86-64 or ARM), macOS (x86-64 or ARM)
- For Linux: *udev* (usually goes together with *systemd*)
