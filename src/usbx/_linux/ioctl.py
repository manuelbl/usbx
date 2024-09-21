# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from ctypes import sizeof
from typing import Type

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT+_IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT+_IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT+_IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


# noinspection PyPep8Naming
def _IOC(dir_: int, type_: str, nr: int, size: int) -> int:  # NOSONAR
    return (dir_ << _IOC_DIRSHIFT) | (ord(type_) << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


# noinspection PyPep8Naming
def _IO(type_: str, nr: int) -> int:  # NOSONAR
    return _IOC(_IOC_NONE, type_, nr, 0)


# noinspection PyPep8Naming
def _IOR(type_: str, nr: int, size: Type) -> int:  # NOSONAR
    return _IOC(_IOC_READ, type_, nr, sizeof(size))


# noinspection PyPep8Naming
def _IOW(type_: str, nr: int, size: Type) -> int:  # NOSONAR
    return _IOC(_IOC_WRITE, type_, nr, sizeof(size))


# noinspection PyPep8Naming
def _IOWR(type_: str, nr: int, size: Type) -> int:  # NOSONAR
    return _IOC(_IOC_READ | _IOC_WRITE, type_, nr, sizeof(size))
