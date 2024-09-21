from dataclasses import dataclass

from usbx import usb, Device, ControlTransfer, RequestType, Recipient, TransferTimeoutError

CC_VIDEO = 0x0E
SC_VIDEOCONTROL = 0x01


def drain_data(endpoint: int) -> None:
    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)
    while True:
        try:
            test_device.transfer_in(endpoint, 0.1)
        except TransferTimeoutError:
            break
    test_device.close()


def enumerate_all_devices() -> None:
    for device in usb.get_devices():
        print(device)

def device_info() -> None:
    for device in usb.get_devices():
        print(f'VID: 0x{device.vid:04x}, PID: 0x{device.pid:04x}')
        print(f'Version: {device.device_version}')
        print(f'Interfaces: {len(device.configuration.interfaces)}')

def is_video_device(device: Device) -> bool:
    for interface in device.configuration.interfaces:
        alternate = interface.current_alternate
        if alternate.class_code == CC_VIDEO and alternate.subclass_code == SC_VIDEOCONTROL:
            return True
    return False

def list_video_cameras() -> None:
    for device in usb.find_devices(match = is_video_device):
        print(device)

def control_request() -> None:
    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    transfer = ControlTransfer(RequestType.VENDOR, Recipient.DEVICE, 0x01, 1234, 0)
    test_device.control_transfer_out(transfer)
    test_device.close()

def interrupt_transfer_out() -> None:
    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)
    test_device.transfer_out(3, bytes([0x56, 0x78, 0x9a, 0xbc]))
    test_device.close()

def interrupt_transfer_in() -> None:
    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)

    test_device.transfer_out(3, bytes([0x56, 0x78, 0x9a, 0xbc]))

    data = test_device.transfer_in(3)
    print(f'Received {len(data)} bytes')

    data = test_device.transfer_in(3)
    print(f'Received {len(data)} bytes')

    test_device.close()

def bulk_transfer_out() -> None:
    test_device = usb.find_device(vid = 0xcafe, pid = 0xceaf)
    test_device.open()
    test_device.claim_interface(0)
    test_device.transfer_out(1, "Hello, world!\n".encode())
    test_device.close()

def bulk_transfer_in() -> None:
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

@dataclass
class DeviceId:
    vid: int
    pid: int
    serial: str

    def matches(self, device: Device) -> bool:
        return (device.vid == self.vid and device.pid == self.pid
            and device.serial == self.serial)

def remembered_device() -> None:
    remembered_device_id = DeviceId(0xcafe, 0xceaf, "35A737883336")

    for device in usb.get_devices():
        if remembered_device_id.matches(device):
            print(f'Remembered device: {device}')
        else:
            print(f'Other device:      {device}')


if __name__ == '__main__':
    drain_data(3)
    drain_data(2)
    enumerate_all_devices()
    device_info()
    list_video_cameras()
    remembered_device()
    control_request()
    interrupt_transfer_out()
    drain_data(3)
    interrupt_transfer_in()
    bulk_transfer_out()
    drain_data(2)
    bulk_transfer_in()