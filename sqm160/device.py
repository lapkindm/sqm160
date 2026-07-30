"""
High-level SQM-160 device interface.

This module combines the USB transport with the protocol layer.
"""

from __future__ import annotations

from .protocol import (
    Response,
    build_command,
    parse_response,
)

from .usb import (
    USBTransport,
    DEFAULT_PRODUCT,
    DEFAULT_MANUFACTURER,
)
from .commands import SQM160Commands


class SQM160(SQM160Commands):
    """
    High-level interface to the INFICON SQM-160.

    Parameters
    ----------
    vid
        USB Vendor ID. If None, automatic discovery is used.

    pid
        USB Product ID. If None, automatic discovery is used.

    product
        USB product string used for automatic discovery.

    manufacturer
        USB manufacturer string used for automatic discovery.

    timeout
        USB read timeout in milliseconds.

    debug
        Enable verbose USB communication logging.

    Example
    -------
    >>> with SQM160() as sqm:
    ...     print(sqm.firmware_version())
    """

    def __init__(
        self,
        *,
        vid: int | None = None,
        pid: int | None = None,
        product: str | None = DEFAULT_PRODUCT,
        manufacturer: str | None = DEFAULT_MANUFACTURER,
        timeout: int = 3000,
        debug: bool = False,
    ) -> None:

        self.transport = USBTransport(
            vid=vid,
            pid=pid,
            product=product,
            manufacturer=manufacturer,
            timeout=timeout,
            debug=debug,
        )

    # --------------------------------------------------------------

    def open(self) -> None:
        """Open the USB connection."""
        self.transport.open()

    # --------------------------------------------------------------

    def close(self) -> None:
        """Close the USB connection."""
        self.transport.close()
        
    # --------------------------------------------------------------

    def reset(self) -> None:
        """Reset the USB connection."""
        self.transport.reset()

    # --------------------------------------------------------------

    def query(self, command: str) -> Response:
        """
        Send a command and return the parsed response.
        """

        packet = build_command(command)

        self.transport.write(packet)

        raw = self.transport.read()

        response = parse_response(raw)
    
        if not response.ok:
            raise SQM160ProtocolError(response.message)
    
        return response

    # --------------------------------------------------------------

    def query_string(self, command: str) -> str:
        return self.query(command).message.strip()

    # --------------------------------------------------------------

    def query_float(self, command: str) -> float:
        return float(self.query_string(command))

    # --------------------------------------------------------------

    def query_int(self, command: str) -> int:
        return int(self.query_string(command))

    # --------------------------------------------------------------


    def query_bool(self, command: str) -> bool:
        """
        Execute a command returning a boolean value.
        """
    
        value = self.query_string(command)
    
        if value == "0":
            return False
    
        if value == "1":
            return True
    
        raise ValueError(
            f"Expected 0 or 1, got {value!r}"
        )


    def query_fields(self, command: str) -> list[str]:
        """
        Execute a command and return whitespace-separated fields.
        """
        return self.query_string(command).split()

        

    def raw_query(self, command: str) -> bytes:
        """
        Send a command and return the raw response bytes.

        Mainly useful while reverse engineering.
        """

        packet = build_command(command)

        self.transport.write(packet)

        return self.transport.read()

    # --------------------------------------------------------------

    def __enter__(self) -> "SQM160":

        self.open()

        return self

    # --------------------------------------------------------------

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ) -> None:

        self.close()