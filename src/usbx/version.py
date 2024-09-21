# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

class Version:
    """
    Semantic version number.

    ``bcd_version`` contains the version: the high byte is the major
    version. The low byte is split into two nibbles (4 bits), the high one
    is the minor version, the lower one is the subminor version. As an example,
    0x0321 represents the version 3.2.1.

    """
    def __init__(self, bcd_version: int):
        self.bcd_version: int = bcd_version
        """Version, encoded as BCD."""

    def __eq__(self, other):
        return self.bcd_version == other.bcd_version

    def __repr__(self):
        return f'{self.major}.{self.minor}.{self.subminor}'

    @property
    def major(self) -> int:
        """Major version."""
        return self.bcd_version >> 8

    @property
    def minor(self) -> int:
        """Minor version."""
        return (self.bcd_version >> 4) & 0x0f

    @property
    def subminor(self) -> int:
        """Subminor version."""
        return self.bcd_version & 0x0f
