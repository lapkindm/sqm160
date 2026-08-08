"""
Low-level RS-232 transport for the INFICON SQM-160.

This module is responsible ONLY for serial communication.

Responsibilities
----------------
- Open and close the RS-232 port
- Configure the serial connection
- Read/write raw SQM-160 protocol packets
- Handle serial communication errors

No protocol framing, command handling, or CRC handling is implemented
here. Packet length information is obtained from the protocol module
only to determine how many bytes must be read.
"""

from __future__ import annotations

from typing import Optional

import serial
from serial import SerialException, SerialTimeoutException

from .exceptions import (
    DeviceNotFoundError,
    SerialCommunicationError,
    SerialTimeoutError,
)
from .protocol import packet_length


# ----------------------------------------------------------------------
# Serial constants
# ----------------------------------------------------------------------

DEFAULT_BAUDRATE = 19200

BYTESIZE = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE

READ_HEADER_SIZE = 2


# ----------------------------------------------------------------------
# Serial transport
# ----------------------------------------------------------------------

class SerialTransport:
    """
    Low-level RS-232 transport for the SQM-160.

    Parameters
    ----------
    port
        Serial port, e.g. ``"/dev/ttyUSB1"``.

    baudrate
        Serial baud rate. The SQM-160 defaults to 19200 baud.

    timeout
        Read timeout in seconds.

    debug
        Print all serial transfers.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = 3.0,
        debug: bool = False,
    ) -> None:

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.debug = debug

        self.ser: Optional[serial.Serial] = None

    # ------------------------------------------------------------------
    # Open / close
    # ------------------------------------------------------------------

    def open(self) -> None:
        """
        Open the RS-232 port.
        """

        if self.ser is not None:
            return

        try:

            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )

        except SerialException as exc:

            self.ser = None

            raise DeviceNotFoundError(
                f"Could not open serial port "
                f"{self.port!r}: {exc}"
            ) from exc

    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Close the RS-232 port and release its resources.
        """

        if self.ser is None:
            return

        try:

            self.ser.close()

        finally:

            self.ser = None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(
        self,
        data: bytes,
    ) -> int:
        """
        Send raw bytes to the SQM-160.
        """

        self._require_open()

        if self.debug:
            print(
                "SERIAL OUT:",
                data.hex(" "),
            )

        try:

            written = self.ser.write(data)

            self.ser.flush()

            return written

        except SerialTimeoutException as exc:

            raise SerialTimeoutError(
                str(exc)
            ) from exc

        except SerialException as exc:

            raise SerialCommunicationError(
                str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self) -> bytes:
        """
        Read one complete SQM-160 response packet.

        The SQM-160 packet contains its length in the second byte.
        Therefore the method first reads the two-byte packet header and
        then reads exactly the remaining number of bytes.

        This is important for commands such as ``W``, whose response
        can be substantially longer than the short responses returned
        by commands such as ``@``.
        """

        self._require_open()

        try:

            # ----------------------------------------------------------
            # Read Sync + Length
            # ----------------------------------------------------------

            header = self.ser.read(READ_HEADER_SIZE)

            if len(header) != READ_HEADER_SIZE:
                raise SerialTimeoutError(
                    "Timed out while reading SQM-160 "
                    "response header."
                )

            if self.debug:
                print(
                    "SERIAL IN :",
                    header.hex(" "),
                )

            # ----------------------------------------------------------
            # Determine complete packet length
            # ----------------------------------------------------------

            total_length = packet_length(header)

            if total_length < READ_HEADER_SIZE:
                raise SerialCommunicationError(
                    f"Invalid SQM-160 packet length: "
                    f"{total_length}"
                )

            # ----------------------------------------------------------
            # Read remaining packet bytes
            # ----------------------------------------------------------

            remaining = total_length - READ_HEADER_SIZE

            body = self.ser.read(remaining)

            if len(body) != remaining:
                raise SerialTimeoutError(
                    "Timed out while reading complete "
                    "SQM-160 response packet."
                )

            data = header + body

            if self.debug:
                print(
                    "SERIAL IN :",
                    data.hex(" "),
                )

            return data

        except SerialTimeoutError:
            raise

        except SerialException as exc:

            raise SerialCommunicationError(
                str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_open(self) -> None:

        if self.ser is None:
            raise RuntimeError(
                "Serial device is not open."
            )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "SerialTransport":

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