"""
High-level SQM-160 device interface.

This module combines the SQM-160 command interface with a transport
layer. The transport can be USB, RS-232, or another implementation
providing the required transport methods.
"""

from __future__ import annotations

from typing import Protocol

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

from .exceptions import ProtocolError


# ----------------------------------------------------------------------
# Transport interface
# ----------------------------------------------------------------------

class Transport(Protocol):
    """
    Interface required by SQM160.

    Both USBTransport and SerialTransport implement this interface.
    """

    def open(self) -> None:
        ...

    def close(self) -> None:
        ...

    def write(self, data: bytes) -> int:
        ...

    def read(self) -> bytes:
        ...


# ----------------------------------------------------------------------
# SQM-160 device
# ----------------------------------------------------------------------

class SQM160(SQM160Commands):
    """
    High-level interface to the INFICON SQM-160.

    By default, the SQM-160 is accessed through USB. A different
    transport can be supplied explicitly, for example SerialTransport
    for an RS-232 connection.

    Parameters
    ----------
    transport
        Communication transport. If None, USBTransport is created.

    vid
        USB Vendor ID. If None, automatic discovery is used.

    pid
        USB Product ID. If None, automatic discovery is used.

    product
        USB product string used for automatic discovery.

    manufacturer
        USB manufacturer string used for automatic discovery.

    timeout
        USB read timeout in milliseconds. Used only when the default
        USB transport is created.

    debug
        Enable verbose communication logging. Used only when the
        default USB transport is created.

    Examples
    --------
    USB:

        with SQM160() as sqm:
            print(sqm.firmware_version())

    RS-232:

        from sqm160 import SQM160, SerialTransport

        transport = SerialTransport(
            "/dev/ttyUSB1",
            debug=True,
        )

        with SQM160(transport=transport) as sqm:
            print(sqm.firmware_version())
    """

    def __init__(
        self,
        *,
        transport: Transport | None = None,
        vid: int | None = None,
        pid: int | None = None,
        product: str | None = DEFAULT_PRODUCT,
        manufacturer: str | None = DEFAULT_MANUFACTURER,
        timeout: int = 3000,
        debug: bool = False,
    ) -> None:

        if transport is None:

            transport = USBTransport(
                vid=vid,
                pid=pid,
                product=product,
                manufacturer=manufacturer,
                timeout=timeout,
                debug=debug,
            )

        self.transport = transport

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def open(self) -> None:
        """
        Open the SQM-160 connection.
        """

        self.transport.open()

    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Close the SQM-160 connection.
        """

        self.transport.close()

    # ------------------------------------------------------------------

    def reset(self) -> None:
        """
        Reset the underlying transport.

        This operation is currently supported by USBTransport and is
        intended for recovering the USB connection. It is not part of
        the SQM-160 command protocol.

        Raises
        ------
        NotImplementedError
            If the selected transport does not provide reset().
        """

        reset = getattr(self.transport, "reset", None)

        if reset is None:
            raise NotImplementedError(
                "The selected transport does not support reset()."
            )

        reset()

    # ------------------------------------------------------------------
    # Protocol
    # ------------------------------------------------------------------

    def query(self, command: str) -> Response:
        """
        Send an SQM-160 command and return the parsed response.
        """

        packet = build_command(command)

        self.transport.write(packet)

        raw = self.transport.read()

        response = parse_response(raw)

        if not response.ok:
            raise ProtocolError(
                response.message
            )

        return response

    # ------------------------------------------------------------------

    def query_string(self, command: str) -> str:
        """
        Execute a command and return its response as a string.
        """

        return self.query(command).message.strip()

    # ------------------------------------------------------------------

    def query_float(self, command: str) -> float:
        """
        Execute a command returning a floating-point value.
        """

        return float(
            self.query_string(command)
        )

    # ------------------------------------------------------------------

    def query_int(self, command: str) -> int:
        """
        Execute a command returning an integer value.
        """

        return int(
            self.query_string(command)
        )

    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------

    def query_fields(
        self,
        command: str,
    ) -> list[str]:
        """
        Execute a command and return whitespace-separated fields.
        """

        return self.query_string(command).split()

    # ------------------------------------------------------------------

    def raw_query(
        self,
        command: str,
    ) -> bytes:
        """
        Send a command and return the raw response bytes.

        Mainly useful for debugging and reverse engineering.
        """

        packet = build_command(command)

        self.transport.write(packet)

        return self.transport.read()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "SQM160":

        self.open()

        return self

    # ------------------------------------------------------------------

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ) -> None:

        self.close()