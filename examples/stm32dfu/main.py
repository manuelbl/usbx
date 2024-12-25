# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import sys
from dfudevice import DFUDevice
from dfuerror import DFUError

# check for single parameter
if len(sys.argv) != 2:
    sys.stderr.write("Usage: dfu_upload <firmware_file>\n")
    sys.exit(1)

# read firmware file
try:
    with open(sys.argv[1], mode='rb') as file:
        firmware = file.read()
except OSError:
    sys.stderr.write(f"Error: Cannot read firmware file {sys.argv[1]}\n")
    sys.exit(2)

# check for single DFU device
devices = DFUDevice.find_devices()
if len(devices) == 0:
    sys.stderr.write("Error: No STM32 DFU device connected (or not in DFU mode)")
    sys.exit(4)
if len(devices) > 1:
    sys.stderr.write("Error: Multiple STM32 DFU devices connected. Please connect only one.")
    sys.exit(4)

device = devices[0]
print(f"DFU device found with serial {device.serial_number}")

# download and verify firmware
try:
    device.open()
    device.download(firmware)
    device.verify(firmware)
    print("Firmware successfully downloaded and verified")

    device.start_application()
    print("DFU mode exited and firmware started")

    device.close()

except DFUError as e:
    sys.stderr.write(f"Error: {e}")
    sys.exit(3)
