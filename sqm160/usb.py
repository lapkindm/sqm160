"""
Low-level USB transport for the INFICON SQM-160.

This module is responsible ONLY for USB communication.

Responsibilities
----------------
- Find the USB device
- Claim/release the USB interface
- Perform the vendor-specific initialization sequence
- Read/write raw USB bulk transfers

No protocol framing or CRC handling is implemented here.
"""

from __future__ import annotations

from typing import Optional

import usb.core
import usb.util

from .exceptions import (
    DeviceBusyError,
    DeviceNotFoundError,
    USBCommunicationError,
    USBTimeoutError,
)

from .protocol import packet_length

# ----------------------------------------------------------------------
# USB constants
# ----------------------------------------------------------------------

DEFAULT_VID = 0x10C4
DEFAULT_PID = 0x83F5

DEFAULT_PRODUCT = "SQM-160 USB"
DEFAULT_MANUFACTURER = "Silicon Labs"


INTERFACE = 0

EP_OUT = 0x01
EP_IN = 0x81

READ_SIZE = 64

# USB control request types
CTRL_OUT = 0x41
CTRL_IN = 0xC0


# ----------------------------------------------------------------------
# USB transport
# ----------------------------------------------------------------------

class USBTransport:
    """
    Low-level USB transport for the SQM-160.

    Parameters
    ----------
    timeout
        Bulk read timeout in milliseconds.

    debug
        Print all USB transfers.
    """


    def __init__(
        self,
        *,
        vid: int | None = None,
        pid: int | None = None,
        manufacturer: str | None = DEFAULT_MANUFACTURER,
        product: str | None = DEFAULT_PRODUCT,
        serial_number: str | None = None,
        timeout: int = 3000,
        debug: bool = False,
    ):
    
        self.vid = vid
        self.pid = pid
        self.manufacturer = manufacturer
        self.product = product
        self.serial_number = serial_number
    
        self.timeout = timeout
        self.debug = debug
    
        self.dev: Optional[usb.core.Device] = None



    def _find_device(self) -> usb.core.Device:
        """
        Locate an SQM-160 USB device.
    
        Search strategy
        ---------------
        1. If both VID and PID are specified, search for that exact device.
        2. Otherwise, enumerate all devices with the requested (or default)
           vendor ID and match the manufacturer and product strings.
    
        Raises
        ------
        DeviceNotFoundError
            If no matching device is found.
    
        DeviceBusyError
            If more than one matching device is found.
        """
    
        # ----------------------------------------------------------
        # Fast path: explicit VID/PID
        # ----------------------------------------------------------
    
        if self.vid is not None and self.pid is not None:
    
            dev = usb.core.find(
                idVendor=self.vid,
                idProduct=self.pid,
            )
    
            if dev is None:
                raise DeviceNotFoundError(
                    f"USB device {self.vid:04X}:{self.pid:04X} not found."
                )
    
            return dev
    
        # ----------------------------------------------------------
        # Automatic discovery
        # ----------------------------------------------------------
    
        vendor = self.vid if self.vid is not None else DEFAULT_VID
    
        candidates = []
    
        for dev in usb.core.find(find_all=True, idVendor=vendor):
    
            try:
            
                manufacturer = (
                    usb.util.get_string(dev, dev.iManufacturer)
                    if dev.iManufacturer
                    else None
                )
            
                product = (
                    usb.util.get_string(dev, dev.iProduct)
                    if dev.iProduct
                    else None
                )
            
                serial = (
                    usb.util.get_string(dev, dev.iSerialNumber)
                    if dev.iSerialNumber
                    else None
                )
            
            except (usb.core.USBError, ValueError):
                continue
            
            if (
                (self.manufacturer is None or manufacturer == self.manufacturer)
                and
                (self.product is None or product == self.product)
                and
                (self.serial_number is None or serial == self.serial_number)
            ):
                candidates.append(dev)
    
        if not candidates:
            raise DeviceNotFoundError(
                "No matching SQM-160 USB device found."
            )
    
        if len(candidates) > 1:
    
            serials = []
    
            for dev in candidates:
                try:
                    serials.append(
                        usb.util.get_string(
                            dev,
                            dev.iSerialNumber,
                        )
                    )
                except (usb.core.USBError, ValueError):
                    serials.append("<unknown>")
    
            raise DeviceBusyError(
                "Multiple matching SQM-160 devices found: "
                + ", ".join(serials)
            )
    
        if self.debug:
            print(
                f"Found SQM-160: "
                f"{manufacturer} | "
                f"{product} | "
                f"SN={serial}"
            )

        return candidates[0]


    
    # ------------------------------------------------------------------

    def open(self) -> None:
        """
        Open the USB device and perform initialization.
        """

        self.dev = self._find_device()
        

        if self.dev is None:
            raise DeviceNotFoundError(
                "SQM-160 USB device not found."
            )

        try:


            if self.dev.is_kernel_driver_active(INTERFACE):
                self.dev.detach_kernel_driver(INTERFACE)


            usb.util.claim_interface(
                self.dev,
                INTERFACE,
            )

            self._initialize()

        except usb.core.USBError as exc:

            self.close()

            raise DeviceBusyError(
                str(exc)
            ) from exc

    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Release all USB resources.
        """

        if self.dev is None:
            return

        try:

            usb.util.release_interface(
                self.dev,
                INTERFACE,
            )

        except Exception:
            pass

        finally:

            usb.util.dispose_resources(self.dev)

            self.dev = None

            
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """
        Reset the USB device.
        """

        self.dev.reset()
        

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
            print("USB OUT :", data.hex(" "))

        try:

            return self.dev.write(
                EP_OUT,
                data,
            )

        except usb.core.USBTimeoutError as exc:

            raise USBTimeoutError(
                str(exc)
            ) from exc

        except usb.core.USBError as exc:

            raise USBCommunicationError(
                str(exc)
            ) from exc

    # ------------------------------------------------------------------

    def read(self) -> bytes:
        """
        Read one complete SQM-160 protocol packet.
    
        The SQM-160 may split a protocol packet across multiple USB bulk
        transfers. This method automatically reassembles the complete
        protocol packet before returning it.
        """
    
        self._require_open()
    
        try:
    
            data = bytearray()
    
            expected_length = None
    
            while True:
    
                chunk = bytes(
                    self.dev.read(
                        EP_IN,
                        READ_SIZE,
                        timeout=self.timeout,
                    )
                )
    
                data.extend(chunk)
    
                # Once the protocol header has been received,
                # determine the total packet length.
                if expected_length is None and len(data) >= 2:
                    expected_length = packet_length(data)
    
                # Stop when the entire protocol packet has been received.
                if (
                    expected_length is not None
                    and len(data) >= expected_length
                ):
    
                    packet = bytes(data[:expected_length])
    
                    if self.debug:
                        print("USB IN  :", packet.hex(" "))
    
                    return packet
    
        except usb.core.USBTimeoutError as exc:
    
            raise USBTimeoutError(
                str(exc)
            ) from exc
    
        except usb.core.USBError as exc:
    
            raise USBCommunicationError(
                str(exc)
            ) from exc


    # ------------------------------------------------------------------

    def ctrl_out(
        self, 
        request: int, 
        value: int, 
        data=None,
    ) -> None:
        """
        Perform a vendor-specific control OUT transfer.
        """
        
        self._require_open()
    
        if self.debug:
            data_str = "<none>" if data is None else data.hex(" ")
            print(
                f"CTRL OUT request={request} "
                f"value=0x{value:04X} "
                f"data={data_str}"
            )
    
        self.dev.ctrl_transfer(
            CTRL_OUT,
            request,
            value,
            0,
            data,
        )


    # ------------------------------------------------------------------

    def ctrl_in(
        self,
        request: int,
        value: int,
        length: int,
    ) -> bytes:
        """
        Perform a vendor-specific control IN transfer.
        """

        self._require_open()

        data = bytes(

            self.dev.ctrl_transfer(
                CTRL_IN,
                request,
                value,
                0,
                length,
            )

        )

        if self.debug:
            print(
                f"CTRL IN  request={request} "
                f"value=0x{value:04X} "
                f"data={data.hex(' ')}"
            )

        return data

    # ------------------------------------------------------------------

    def _initialize(self) -> None:
        """
        Vendor-specific initialization sequence.

        This sequence was reverse engineered from the official
        Windows software using USBPcap.
        """

        self.ctrl_out(
            request=0,
            value=0x0000,
        )

        self.ctrl_in(
            request=255,
            value=0x370B,
            length=1,
        )

        self.ctrl_out(
            request=0,
            value=0xFFFF,
        )

        self.ctrl_out(
            request=30,
            value=0x0000,
            data=b"\x00\xC2\x01\x00",
        )

    # ------------------------------------------------------------------

    def _require_open(self) -> None:

        if self.dev is None:
            raise RuntimeError(
                "USB device is not open."
            )

    # ------------------------------------------------------------------

    def __enter__(self) -> "USBTransport":

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