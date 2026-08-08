"""
Python interface for the INFICON SQM-160.

Example
-------
>>> from sqm160 import SQM160

>>> with SQM160() as sqm:
...     print(sqm.firmware_version())
"""

from .serial import SerialTransport

from .device import SQM160

from .models import (
    SensorMeasurement,
    FilmParameters,
    SystemParameters,
    SystemParameters2,
    DisplayMode,
)

from .exceptions import (
    SQM160Error,
    DeviceNotFoundError,
    DeviceBusyError,
    USBCommunicationError,
    USBTimeoutError,
    ProtocolError,
    CRCError,
)

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("sqm160")
except PackageNotFoundError:
    __version__ = "unknown"
    

__all__ = [
    "SQM160",
    "SerialTransport",

    # Data models
    "SensorMeasurement",
    "FilmParameters",
    "SystemParameters",
    "SystemParameters2",
    "DisplayMode",

    # Exceptions
    "SQM160Error",
    "DeviceNotFoundError",
    "DeviceBusyError",
    "ProtocolError",
    "CRCError",
    "USBCommunicationError",
    "USBTimeoutError",
    "ProtocolError",
    "CRCError",
]