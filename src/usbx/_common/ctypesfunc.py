# usbx – Accessing USB devices
# Copyright (c) 2024 Manuel Bleichenbacher
# Licensed under MIT License
# https://opensource.org/licenses/MIT

from ctypes import POINTER, cast, c_uint8, c_void_p

from typing import TypeVar

T = TypeVar('T', bound=POINTER)


def readable_buffer(data: bytes, target_type: type[T] = c_void_p) -> T:
    """
    Creates a *ctypes* instance for the given data.

    The returned instance is of the specified *ctypes* type.

    :param data: data to convert to a *ctypes* buffer
    :param target_type: type of resulting pointer (defaults to ``c_void_p``).
    :return: *ctypes* pointer
    """
    return cast((c_uint8 * len(data)).from_buffer_copy(data), target_type)


def writable_buffer(data: bytearray, target_type: type[T] = c_void_p) -> T:
    """
    Creates a writable *ctypes* instance sharing the buffer with the given data.

    The returned instance is of the specified *ctypes* type.

    :param data: data convert to a *ctypes* instance
    :param target_type: type of resulting pointer (defaults to ``c_void_p``).
    :return: *ctypes* pointer
    """
    return cast((c_uint8 * len(data)).from_buffer(data), target_type)
