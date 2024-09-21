from dataclasses import dataclass
from typing import Optional

from usbx import usb, Device, Interface, AlternateInterface, Endpoint


@dataclass
class ClassCode:
    class_code: int
    name: str


@dataclass
class SubclassCode:
    class_code: int
    subclass_code: int
    name: str


@dataclass
class ProtocolCode:
    protocol_code: int
    class_code: int
    subclass_code: int
    name: str


class ClassInfo:
    def __init__(self):
        self.class_codes: list[ClassCode] = []
        self.subclass_codes: list[SubclassCode] = []
        self.protocol_codes: list[ProtocolCode] = []

    def lookup_class_code(self, class_code: int) -> Optional[str]:
        return next((code.name for code in self.class_codes if code.class_code == class_code), None)

    def lookup_subclass_code(self, class_code: int, subclass_code: int) -> Optional[str]:
        return next((code.name for code in self.subclass_codes
                     if code.class_code == class_code and code.subclass_code == subclass_code), None)

    def lookup_protocol_code(self, class_code: int, subclass_code: int, protocol_code: int) -> Optional[str]:
        return next((code.name for code in self.protocol_codes
                     if code.class_code == class_code and code.subclass_code == subclass_code
                     and code.protocol_code == protocol_code), None)

    def load(self):
        class_code = 0
        subclass_code = 0
        for line in usb_class_info_data.splitlines():
            if line.startswith('..'):
                protocol_code = int(line[2:4], 16)
                self.protocol_codes.append(ProtocolCode(protocol_code, subclass_code, class_code, line[6:]))
            elif line.startswith('.'):
                subclass_code = int(line[1:3], 16)
                self.subclass_codes.append(SubclassCode(subclass_code, class_code, line[5:]))
            elif line.startswith('C '):
                class_code = int(line[2:4], 16)
                self.class_codes.append(ClassCode(class_code, line[6:]))


class_info = ClassInfo()


def print_device(device: Device) -> None:
    print('Device:')
    print(f'  VID: 0x{device.vid:04x}')
    print(f'  PID: 0x{device.pid:04x}')
    if device.manufacturer is not None:
        print(f'  Manufacturer:  {device.manufacturer}')
    if device.product is not None:
        print(f'  Product name:  {device.product}')
    if device.serial is not None:
        print(f'  Serial number: {device.serial}')
    print(f'  Device class:    0x{device.class_code:02x}', end='')
    print_code(class_info.lookup_class_code(device.class_code))
    print(f'  Device subclass: 0x{device.subclass_code:02x}', end='')
    print_code(class_info.lookup_subclass_code(device.class_code, device.subclass_code))
    print(f'  Device protocol: 0x{device.protocol_code:02x}', end='')
    print_code(class_info.lookup_protocol_code(device.class_code, device.subclass_code, device.protocol_code))

    for intf in device.configuration.interfaces:
        print_interface(intf)

    print_raw_descriptor("Device descriptor", device.device_descriptor)
    print_raw_descriptor("Configuration descriptor", device.configuration_descriptor)

    print()
    print()


def print_interface(intf: Interface) -> None:
    for alt in intf.alternates:
        print_alternate(alt, intf.number, alt == intf.current_alternate)


def print_alternate(alternate: AlternateInterface, intf_number: int, is_defaut: bool) -> None:
    print()
    if is_defaut:
        print(f'  Interface {intf_number}')
    else:
        print(f'  Interface {intf_number} (alternate {alternate.number})')

    print(f'    Interface class:    0x{alternate.class_code:02x}', end='')
    print_code(class_info.lookup_class_code(alternate.class_code))
    print(f'    Interface subclass: 0x{alternate.subclass_code:02x}', end='')
    print_code(class_info.lookup_subclass_code(alternate.class_code, alternate.subclass_code))
    print(f'    Interface protocol: 0x{alternate.protocol_code:02x}', end='')
    print_code(class_info.lookup_protocol_code(alternate.class_code, alternate.subclass_code, alternate.protocol_code))

    for endpoint in alternate.endpoints:
        print_endpoint(endpoint)


def print_endpoint(endpoint: Endpoint) -> None:
    print()
    print(f'    Endpoint {endpoint.number}')
    print(f'      Direction: {endpoint.direction.name}')
    print(f'      Transfer type: {endpoint.transfer_type.name}')
    print(f'      Packet size: {endpoint.max_packet_size} bytes')


def print_code(code: Optional[str]) -> None:
    if code is not None:
        print(f' ({code})')
    else:
        print()


def print_raw_descriptor(title: str, descriptor: bytes) -> None:
    print()

    length = len(descriptor)
    print(f'  {title} ({length} bytes)')

    i = 0
    while i < length:
        print(f'    {i:04x} ', end='')
        for j in range(i, min(i + 16, length)):
            print(f' {descriptor[j]:02x}', end='')
        print()
        i += 16


usb_class_info_data = """
C 00  (Defined at Interface level)
C 01  Audio
.01  Control Device
.02  Streaming
.03  MIDI Streaming
C 02  Communications
.01  Direct Line
.02  Abstract (modem)
..00  None
..01  AT-commands (v.25ter)
..02  AT-commands (PCCA101)
..03  AT-commands (PCCA101 + wakeup)
..04  AT-commands (GSM)
..05  AT-commands (3G)
..06  AT-commands (CDMA)
..fe  Defined by command set descriptor
..ff  Vendor Specific (MSFT RNDIS?)
.03  Telephone
.04  Multi-Channel
.05  CAPI Control
.06  Ethernet Networking
.07  ATM Networking
.08  Wireless Handset Control
.09  Device Management
.0a  Mobile Direct Line
.0b  OBEX
.0c  Ethernet Emulation
..07  Ethernet Emulation (EEM)
C 03  Human Interface Device
.00  No Subclass
..00  None
..01  Keyboard
..02  Mouse
.01  Boot Interface Subclass
..00  None
..01  Keyboard
..02  Mouse
C 05  Physical Interface Device
C 06  Imaging
.01  Still Image Capture
..01  Picture Transfer Protocol (PIMA 15470)
C 07  Printer
.01  Printer
..00  Reserved/Undefined
..01  Unidirectional
..02  Bidirectional
..03  IEEE 1284.4 compatible bidirectional
..ff  Vendor Specific
C 08  Mass Storage
.01  RBC (typically Flash)
..00  Control/Bulk/Interrupt
..01  Control/Bulk
..50  Bulk-Only
.02  SFF-8020i, MMC-2 (ATAPI)
.03  QIC-157
.04  Floppy (UFI)
..00  Control/Bulk/Interrupt
..01  Control/Bulk
..50  Bulk-Only
.05  SFF-8070i
.06  SCSI
..00  Control/Bulk/Interrupt
..01  Control/Bulk
..50  Bulk-Only
C 09  Hub
.00  Unused
..00  Full speed (or root) hub
..01  Single TT
..02  TT per port
C 0a  CDC Data
.00  Unused
..30  I.430 ISDN BRI
..31  HDLC
..32  Transparent
..50  Q.921M
..51  Q.921
..52  Q.921TM
..90  V.42bis
..91  Q.932 EuroISDN
..92  V.120 V.24 rate ISDN
..93  CAPI 2.0
..fd  Host Based Driver
..fe  CDC PUF
..ff  Vendor specific
C 0b  Chip/SmartCard
C 0d  Content Security
C 0e  Video
.00  Undefined
.01  Video Control
.02  Video Streaming
.03  Video Interface Collection
C 0f  Personal Healthcare
C 10  Audio/Video
.01  AVData Control
.02  AVData Video Stream
.03  AVData Audio Stream
C 11  Billboard
C 12  Type-C Bridge
C 13  Bulk Display
C 14  MCTCP over USB
.00  MCTCP Management
..01  MCTCP 1.x
..02  MCTCP 2.x
.01  MCTCP Host
..01  MCTCP 1.x
..02  MCTCP 2.x
C 3c  I3C
C 58  Xbox
.42  Controller
C dc  Diagnostic
.01  Reprogrammable Diagnostics
..01  USB2 Compliance
C e0  Wireless
.01  Radio Frequency
..01  Bluetooth
..02  Ultra WideBand Radio Control
..03  RNDIS
.02  Wireless USB Wire Adapter
..01  Host Wire Adapter Control/Data Streaming
..02  Device Wire Adapter Control/Data Streaming
..03  Device Wire Adapter Isochronous Streaming
C ef  Miscellaneous Device
.01  ?
..01  Microsoft ActiveSync
..02  Palm Sync
.02  ?
..01  Interface Association
..02  Wire Adapter Multifunction Peripheral
.03  ?
..01  Cable Based Association
.05  USB3 Vision
C fe  Application Specific Interface
.01  Device Firmware Update
.02  IRDA Bridge
.03  Test and Measurement
..01  TMC
..02  USB488
C ff  Vendor Specific Class
.ff  Vendor Specific Subclass
..ff  Vendor Specific Protocol
"""


if __name__ == '__main__':
    class_info.load()
    for dev in usb.get_devices():
        print_device(dev)
