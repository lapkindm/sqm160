"""
Exceptions used by the SQM-160 package.
"""


class SQM160Error(Exception):
    """Base class for all SQM-160 exceptions."""


class DeviceNotFoundError(SQM160Error):
    """The SQM-160 USB device could not be found."""


class DeviceBusyError(SQM160Error):
    """The SQM-160 USB interface is already in use."""


class USBCommunicationError(SQM160Error):
    """A USB communication error occurred."""


class USBTimeoutError(USBCommunicationError):
    """The device did not respond before the timeout expired."""


class ProtocolError(SQM160Error):
    """Malformed protocol packet or unexpected response."""


class CRCError(ProtocolError):
    """CRC verification failed."""