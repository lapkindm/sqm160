"""
INFICON SQM-160 communication protocol.

This module implements the packet framing described in the SQM-160
communications manual.

Command packet:

    ! <length+34> <message> CRC1 CRC2

Response packet:

    ! <length+35> <status> <message> CRC1 CRC2
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exceptions import CRCError, ProtocolError


SYNC = ord("!")

COMMAND_LENGTH_OFFSET = 34
RESPONSE_LENGTH_OFFSET = 35

CRC_INIT = 0x3FFF
CRC_POLY = 0x2001


# ======================================================================
# Response status
# ======================================================================

class ResponseStatus(Enum):
    """
    SQM-160 response status.
    """

    OK = "A"
    INVALID_COMMAND = "C"
    INVALID_DATA = "D"

    @classmethod
    def from_char(cls, value: str) -> "ResponseStatus":
        try:
            return cls(value)
        except ValueError:
            raise ProtocolError(f"Unknown response status '{value}'.")


# ======================================================================
# Parsed response
# ======================================================================

@dataclass(frozen=True)
class Response:
    """
    Parsed SQM-160 response.
    """

    status: ResponseStatus
    message: str
    raw: bytes

    @property
    def ok(self) -> bool:
        return self.status is ResponseStatus.OK


# ======================================================================
# CRC
# ======================================================================

def crc14(data: bytes) -> int:
    """
    Calculate the SQM-160 14-bit CRC.

    Parameters
    ----------
    data
        Everything except Sync and CRC bytes.
    """

    crc = CRC_INIT

    for byte in data:

        crc ^= byte

        for _ in range(8):

            carry = crc & 1

            crc >>= 1

            if carry:
                crc ^= CRC_POLY

    return crc & 0x3FFF


def crc_bytes(data: bytes) -> tuple[int, int]:
    """
    Convert CRC to transmitted CRC1/CRC2 bytes.
    """

    crc = crc14(data)

    crc1 = (crc & 0x7F) + COMMAND_LENGTH_OFFSET
    crc2 = ((crc >> 7) & 0x7F) + COMMAND_LENGTH_OFFSET

    return crc1, crc2


# ======================================================================
# Commands
# ======================================================================

def build_command(command: str) -> bytes:
    """
    Build a command packet.

    Example
    -------
    >>> build_command("@")
    b'!#@O7'
    """

    message = command.encode("ascii")

    if len(message) > 190:
        raise ValueError("Command is too long.")

    body = bytes([len(message) + COMMAND_LENGTH_OFFSET]) + message

    crc1, crc2 = crc_bytes(body)

    return bytes([SYNC]) + body + bytes([crc1, crc2])


# ======================================================================
# Packet verification
# ======================================================================

def verify_crc(packet: bytes, length_offset: int) -> bool:
    """
    Verify packet CRC.

    Parameters
    ----------
    packet
        Complete packet.

    length_offset
        34 for commands, 35 for responses.
    """

    if len(packet) < 5:
        return False

    if packet[0] != SYNC:
        return False

    body = packet[1:-2]

    crc = crc14(body)

    crc1 = (crc & 0x7F) + COMMAND_LENGTH_OFFSET
    crc2 = ((crc >> 7) & 0x7F) + COMMAND_LENGTH_OFFSET

    if packet[-2] != crc1:
        return False

    if packet[-1] != crc2:
        return False

    expected = (packet[1] - length_offset) + 4

    return expected == len(packet)


def packet_length(packet: bytes | bytearray) -> int:
    """
    Return the total length of an SQM-160 protocol packet.
    """

    if len(packet) < 2:
        raise ProtocolError("Packet header incomplete.")

    response_length = packet[1] - RESPONSE_LENGTH_OFFSET

    return response_length + 4

# ======================================================================
# Responses
# ======================================================================

def parse_response(packet: bytes) -> Response:
    """
    Parse an SQM-160 response packet.

    Raises
    ------
    ProtocolError
    CRCError
    """

    if len(packet) < 5:
        raise ProtocolError("Packet too short.")

    if packet[0] != SYNC:
        raise ProtocolError("Invalid sync character.")

    response_length = packet[1] - RESPONSE_LENGTH_OFFSET

    expected_length = response_length + 4

    if len(packet) != expected_length:
        raise ProtocolError(
            f"Expected {expected_length} bytes, got {len(packet)}."
        )

    if response_length < 1:
        raise ProtocolError("Response has no status character.")

    if not verify_crc(packet, RESPONSE_LENGTH_OFFSET):
        raise CRCError("CRC verification failed.")

    status = ResponseStatus.from_char(chr(packet[2]))

    message_length = response_length - 1

    message = packet[
        3 : 3 + message_length
    ].decode("ascii")

    return Response(
        status=status,
        message=message,
        raw=packet,
    )