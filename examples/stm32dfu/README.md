# Device Firmware Upload (DFU) for STM32

This sample programs implements firmware upload for STM32 microcontrollers with the built-in DFU mode.

## Prerequisites

- Python 3.9 or higher
- 64-bit operating system (Windows, macOS, Linux)

## How to run

### Install usbx library

```shell
pip install -r requirements.txt
```

### Put the STM32 development board in DFU mode

- Connect an STM32 development board (like a BlackPill board) to your computer while pressing the *Boot* button.
- Ensure that the device is in DFU mode by checking macOS *System Information* or Windows *Device Manager*. The device should appear as "STM32 BOOTLOADER".

On Windows, the *WinUSB* driver must be installed. See [DFU on Windows](https://github.com/manuelbl/JavaDoesUSB/wiki/DFU-on-Windows) for additional information.

On many Linux distributions, the default permissions do not allow access to USB devices. To change it, create a file `/etc/udev/rules.d/50-stm-dfu.rules` with the below content:

```text
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="df11", MODE="0666"
```

Then disconnect and reconnect the the USB device.


### Run the application

Run the command below (using a suitable firmware file for your device):

```shell
$ python main.py blackpill-f401cc.bin
DFU device found with serial 35A737883336.
Target memory segment: Internal Flash
Erasing page at 0x8000000 (size 0x4000)
Writing data at 0x8000000 (size 0x800)
Writing data at 0x8000800 (size 0x800)
Writing data at 0x8001000 (size 0x800)
Writing data at 0x8001800 (size 0x800)
Writing data at 0x8002000 (size 0x800)
Writing data at 0x8002800 (size 0x1f4)
Firmware successfully downloaded and verified
DFU mode exited and firmware started
```
