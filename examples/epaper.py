# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import struct
import time
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageOps

from usbx import Device, usb


class Status(object):
    """Status information sent by display"""
    def __init__(self, data: bytes):
        (sequence, data_left, result) = struct.unpack('<IIB', data[0:9])
        self.sequence: int = sequence
        self.data_left: int = data_left
        self.result: int = result


class DisplayInfo(object):
    """Information about display (result of ``GET_SYS_CMD`` command)"""

    LENGTH: int = 112

    def __init__(self, data: bytes):
        x = struct.unpack('>IIIIIIIIIIIIIIIIIII', data[0:76])
        self.standard_cmd_no: int = x[0]
        self.extended_cmd_no: int = x[1]
        self.signature: int = x[2]
        self.version: int = x[3]
        self.width: int = x[4]
        self.height: int = x[5]
        self.update_buf_base: int = x[6]
        self.image_buf_base: int = x[7]
        self.temperature_no: int = x[8]
        self.mode_no: int = x[9]
        self.frame_count: [int] = x[10:17]
        self.num_image_buf: int = x[18]


@dataclass
class Area:
    """Area in buffer (parameter for ``LD_IMG_AREA_CMD`` command)"""
    address: int = 0
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

    def to_bytes(self) -> bytes:
        return struct.pack('>IIIII', self.address, self.x, self.y, self.w, self.h)


@dataclass
class DisplayArea:
    """Area on display (parameter for ``DPY_AREA_CMD`` command)"""
    address: int = 0
    mode: int = 0
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    wait_ready: int = 0

    def to_bytes(self) -> bytes:
        return struct.pack('>IIIIIII', self.address, self.mode, self.x, self.y, self.w, self.h, self.wait_ready)


class Display(object):
    """E-paper display (with IT8951 controller)"""
    ENDPOINT_IN: int = 1
    ENDPOINT_OUT: int = 2

    GET_SYS_CMD: bytes = bytes([0xfe, 0, 0x38, 0x39, 0x35, 0x31, 0x80, 0, 0x01, 0, 0x02, 0, 0, 0, 0, 0])
    LD_IMG_AREA_CMD: bytes = bytes([0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa2, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    DPY_AREA_CMD: bytes = bytes([0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x94, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def __init__(self):
        self.device: Optional[Device] = None
        self.sequence_no: int = 1
        self.display_info: Optional[DisplayInfo] = None

    def open(self):
        """Open communication to display"""
        self.device = usb.find_device(vid=0x048d, pid=0x8951)
        if self.device is None:
            raise ValueError('Device not found')
        self.device.detach_standard_drivers()
        time.sleep(1)
        self.device.open()
        self.device.claim_interface(0)
        self.display_info = DisplayInfo(self.read_command(Display.GET_SYS_CMD, DisplayInfo.LENGTH))

    def close(self):
        """Close communication to display"""
        self.device.close()
        self.device.attach_standard_drivers()

    def display_image(self, image: Image.Image):
        """
        Display PIL image on display

        The image must have the same size as the display,
        and it must be grayscale image using the values 0 to 15 for each pixel.
        """
        width = image.width
        height = image.height
        address = display.display_info.image_buf_base

        # split into bands to not exceeding 60KB
        band_height = (60000 - 20) // width
        y_offset = 0
        while y_offset < height:
            band_height_2 = min(band_height, height - y_offset)
            band = image.crop((0, y_offset, width, y_offset + band_height_2))
            pixels = bytearray(band_height_2 * width)
            index = 0
            for pixel in band.getdata():
                pixels[index] = pixel
                index += 1
            self.load_image_area(Area(address, 0, y_offset, width, band_height_2), pixels)
            y_offset += band_height

        self.display_area(DisplayArea(address, 2, 0, 0, width, height, 1))

    def load_image_area(self, area: Area, pixel_data: bytes) -> None:
        self.write_command(Display.LD_IMG_AREA_CMD, area.to_bytes(), pixel_data)

    def display_area(self, area: DisplayArea) -> None:
        self.write_command(Display.DPY_AREA_CMD, area.to_bytes())

    def read_command(self, command: bytes, expected_length: int) -> bytes:
        cmd = self.create_command_block(command, expected_length, True)
        self.device.transfer_out(Display.ENDPOINT_OUT, cmd)
        result = self.device.transfer_in(Display.ENDPOINT_IN, 1.0)
        self.read_status()
        return result

    def write_command(self, command: bytes, data1: bytes, data2: bytes = None) -> None:
        cmd = self.create_command_block(command, len(data1) + (len(data2) if data2 is not None else 0), False)
        self.device.transfer_out(Display.ENDPOINT_OUT, cmd)
        self.device.transfer_out(Display.ENDPOINT_OUT, data1)
        if data2 is not None:
            self.device.transfer_out(Display.ENDPOINT_OUT, data2)
        self.read_status()

    def read_status(self) -> Status:
        result = self.device.transfer_in(Display.ENDPOINT_IN, 1.0)
        if len(result) != 13:
            raise ValueError(f'Unexpected length of status block: {len(result)}')
        return Status(result)

    def create_command_block(self, command: bytes, data_length: int, direction_in: bool) -> bytes:
        header = struct.pack('<IIIBBB', 0x43425355, self.sequence_no, data_length,
                             0x80 if direction_in else 0x00, 0, len(command))
        self.sequence_no += 1
        return header + command

if __name__ == '__main__':
    display = Display()
    display.open()

    # load image, resize and crop to display size and quantize to 4-bit grayscale
    tiger = Image.open('tiger.jpg')
    tiger = ImageOps.fit(tiger, (display.display_info.width, display.display_info.height))
    palette_image = Image.new('P', (16, 16))
    palette_image.putpalette([0, 0, 0, 17, 17, 17, 34,34, 34, 51, 51, 51, 68, 68, 68, 85, 85, 85, 102, 102, 102,
                              119, 119, 119, 136, 136, 136, 153, 153, 153, 170, 170, 170, 187, 187, 187, 187,
                              204, 204, 204, 221, 221, 221, 238, 238, 238, 255, 255, 255])
    tiger = tiger.quantize(colors=16, palette=palette_image)
    tiger = ImageOps.grayscale(tiger)

    display.display_image(tiger)

    display.close()
