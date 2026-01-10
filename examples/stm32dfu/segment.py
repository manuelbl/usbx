# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

import re
from dataclasses import dataclass
from typing import Optional

from usbx import ControlTransfer, Device, Recipient, RequestType


class Segment:
    """
    Represents a memory segment of the USB device, be it flash memory, RAM or any other type.
    """
    
    def __init__(self, alt_setting: int, descriptor: str):
        """
        Creates a new instance.

        The segment descriptor is the name of the USB alternate interface setting.
        """

        # The format is described in "UM0424 STM32 USB-FS-Device development kit", ch. 10.3.2

        self.alt_setting: int = alt_setting
        """Alternate setting number"""
        
        self.sectors: list[Page] = []
        """Sectors within the segment"""

        match = Segment.segment_pattern.match(descriptor)

        self.name: str = match.group(1).strip()
        """Segment name"""

        start_address = int(match.group(2), 16)
        while True:
            match = Segment.sector_pattern.match(descriptor, pos=match.end())
            if match is None:
                break

            count = int(match.group(1))
            size = int(match.group(2))
            multiplier = match.group(3)
            attributes = ord(match.group(4)[0]) - 0x60

            match multiplier:
                case "K":
                    size *= 1024
                case "M":
                    size *= 1024 * 1024
            
            self.sectors.append(Page(self, start_address, count, size, attributes))
            start_address += size


    @staticmethod
    def get_segments(device: Device, interface_number: int) -> list['Segment']:
        result: list['Segment'] = []

        # STM uses multiple alternate interface settings to represent segments.
        # The alternate interface setting names describes the sectors within the segment.
        descriptor = device.configuration_descriptor
        offset = 0
        while offset < len(descriptor):
            if descriptor[offset + 1] == 4 and descriptor[offset + 2] == interface_number:
                alt_setting = descriptor[offset + 3]
                string_index = descriptor[offset + 8]
                alt_setting_name = Segment.get_string_descriptor(device, string_index)
                result.append(Segment(alt_setting, alt_setting_name))
            offset += descriptor[offset]
        return result

    @staticmethod
    def get_string_descriptor(device: Device, index: int):
        setup = ControlTransfer(RequestType.STANDARD, Recipient.DEVICE, 6, (3 << 8) | index, 0)
        string_desc = device.control_transfer_in(setup, 255)
        byte_end = len(string_desc) // 2 * 2  # round to multiple of 2
        return string_desc[2:byte_end].decode('utf-16')
    
    @staticmethod
    def find_page(segments: list['Segment'], address: int) -> Optional['Page']:
        """
        Gets the page for the specified address.
        """
        for segment in segments:
            for sector in segment.sectors:
                if sector.start_address <= address < sector.end_address:
                    offset = address - sector.start_address
                    page_number = offset // sector.page_size
                    return Page(segment, sector.start_address + page_number * sector.page_size, 1, sector.page_size, sector.attributes)
        return None
    
    segment_pattern = re.compile(r"@([^/]+)/0x([0-9A-Fa-f]+)/")
    sector_pattern = re.compile(r",?(\d+)\*(\d+) ?([BKM]?)(.)")


@dataclass
class Page:
    """
    Page of flash memory, RAM or other type of memory.

    If count is > 1, it represents a sector consisting of multiple equal pages.
    """

    segment: 'Segment'
    """memory segment this page belongs to"""

    start_address: int
    """start address"""

    count: int
    """number of pages"""

    page_size: int
    """page size (in bytes)"""

    attributes: int
    """page attributes"""


    @property
    def end_address(self) -> int:
       """end address of the page or sector"""
       return self.start_address + self.count * self.page_size

    @property
    def is_readable(self) -> bool:
       """Indicates if the page or sector is readable"""
       return (self.attributes & 1) != 0

    @property
    def is_erasable(self) -> bool:
       """Indicates if the page or sector is erasable"""
       return (self.attributes & 2) != 0

    @property
    def is_writable(self) -> bool:
       """Indicates if the page or sector is writable"""
       return (self.attributes & 4) != 0
