"""
Data models for the INFICON SQM-160.

Each model represents a structured record exchanged with the controller.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from dataclasses import dataclass, replace, field

from enum import IntEnum


# ----------------------------------------------------------------------
# Enumerations
# ----------------------------------------------------------------------

class DisplayMode(IntEnum):
    """
    Rate/Thickness display mode.
    """

    ANGSTROM = 0
    NANOMETER = 1
    FREQUENCY = 2
    MASS = 3

# ----------------------------------------------------------------------
# Base class
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SQMModel(ABC):
    """
    Base class for all SQM-160 data models.
    """

    @classmethod
    @abstractmethod
    def parse(cls, fields: list[str]):
        """
        Construct the model from protocol fields.
        """
        raise NotImplementedError

    @abstractmethod
    def serialize(self) -> list[str]:
        """
        Convert the model into protocol fields.
        """
        raise NotImplementedError

    def copy(self, **changes):
        """
        Return a copy of the model with selected fields modified.
        """
        return replace(self, **changes)

# ----------------------------------------------------------------------
# Measurement models
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SensorMeasurement:
    """
    Current measurement of one sensor.

    Used by command W.
    """

    rate: float
    thickness: float
    frequency: float

    @classmethod
    def parse(
        cls,
        fields: list[str],
    ) -> "SensorMeasurement":

        if len(fields) != 3:
            raise ValueError(
                f"Expected 3 fields, got {len(fields)}."
            )

        return cls(
            rate=float(fields[0]),
            thickness=float(fields[1]),
            frequency=float(fields[2]),
        )

    @classmethod
    def parse_measurements(
        cls,
        fields: list[str],
    ) -> dict[int, "SensorMeasurement"]:
        """
        Parse the response of command W.
        """

        if not fields:
            return {}

        # Ignore the leading dummy value
        fields = fields[1:]

        if len(fields) % 3 != 0:
            raise ValueError(
                f"Expected a multiple of 3 fields, got {len(fields)}."
            )

        return {
            sensor: cls.parse(fields[i:i + 3])
            for sensor, i in enumerate(range(0, len(fields), 3), start=1)
        }


# ----------------------------------------------------------------------
# System parameter models
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class SystemParameters(SQMModel):
    """
    System 1 parameters.

    Used by command:
        B
    """

    time_base: float

    simulate_mode: bool

    display_mode: DisplayMode

    high_rate_resolution: bool

    rate_filter: int

    crystal_tooling: tuple[int, int, int, int, int, int]

    @classmethod
    def parse(
        cls,
        fields: list[str],
    ) -> "SystemParameters":

        if len(fields) != 11:
            raise ValueError(
                f"Expected 11 fields, got {len(fields)}."
            )

        return cls(
            time_base=float(fields[0]),
            simulate_mode=bool(int(fields[1])),
            display_mode=DisplayMode(int(fields[2])),
            high_rate_resolution=bool(int(fields[3])),
            rate_filter=int(fields[4]),
            crystal_tooling=tuple(
                int(x)
                for x in fields[5:11]
            ),
        )

    def serialize(self) -> list[str]:

        return [
            f"{self.time_base:.2f}",
            str(int(self.simulate_mode)),
            str(int(self.display_mode)),
            str(int(self.high_rate_resolution)),
            str(self.rate_filter),
            *(str(x) for x in self.crystal_tooling),
        ]

    def tooling(
        self,
        sensor: int,
    ) -> int:
        """
        Return the crystal tooling for one sensor.

        Parameters
        ----------
        sensor
            Sensor number (1–6).
        """

        if not 1 <= sensor <= 6:
            raise ValueError(
                "Sensor number must be between 1 and 6."
            )

        return self.crystal_tooling[sensor - 1]


@dataclass(frozen=True)
class SystemParameters2(SQMModel):
    """
    System 2 parameters.

    Used by command C.
    """

    min_frequency: float
    max_frequency: float

    min_rate: float
    max_rate: float

    min_thickness: float
    max_thickness: float

    etch_mode: bool

    @classmethod
    def parse(
        cls,
        fields: list[str],
    ) -> "SystemParameters2":

        if len(fields) != 7:
            raise ValueError(
                f"Expected 7 fields, got {len(fields)}."
            )

        return cls(
            min_frequency=float(fields[0]),
            max_frequency=float(fields[1]),
            min_rate=float(fields[2]),
            max_rate=float(fields[3]),
            min_thickness=float(fields[4]),
            max_thickness=float(fields[5]),
            etch_mode=bool(int(fields[6])),
        )

    def serialize(self) -> list[str]:

        return [
            f"{self.min_frequency:.3f}",
            f"{self.max_frequency:.3f}",
            f"{self.min_rate:.3f}",
            f"{self.max_rate:.3f}",
            f"{self.min_thickness:.3f}",
            f"{self.max_thickness:.3f}",
            str(int(self.etch_mode)),
        ]


# ----------------------------------------------------------------------
# Film models
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class FilmParameters(SQMModel):
    """
    Film parameters.

    Used by command A.
    """

    film_number: int

    name: str

    density: float

    tooling: int

    z_ratio: float

    final_thickness: float

    thickness_setpoint: float

    time_setpoint: int

    active_sensors: tuple[int, ...]

    
    @classmethod
    def parse(
        cls,
        film_number: int,
        message: str,
    ) -> "FilmParameters":
        """
        Parse the response of command A.
        """
    
        # ------------------------------------------------------------------
        # Film name occupies the first 8 characters.
        # ------------------------------------------------------------------
    
        name = message[:8].rstrip()
    
        # ------------------------------------------------------------------
        # Remaining fields are whitespace-separated.
        # ------------------------------------------------------------------
    
        fields = message[8:].split()
    
        if len(fields) != 7:
            raise ValueError(
                f"Expected 7 fields after film name, got {len(fields)}."
            )
    
        mask = int(fields[6])
    
        active_sensors = tuple(
            sensor
            for sensor in range(1, 7)
            if mask & (1 << (sensor - 1))
        )
    
        return cls(
            film_number=film_number,
            name=name,
            density=float(fields[0]),
            tooling=int(fields[1]),
            z_ratio=float(fields[2]),
            final_thickness=float(fields[3]),
            thickness_setpoint=float(fields[4]),
            time_setpoint=int(fields[5]),
            active_sensors=active_sensors,
        )


        

    def serialize(self) -> list[str]:
    
        mask = sum(
            1 << (sensor - 1)
            for sensor in self.active_sensors
        )
    
        return [
            self.name.upper()[:8].ljust(8),
            f"{self.density:.2f}",
            str(self.tooling),
            f"{self.z_ratio:.3f}",
            f"{self.final_thickness:.3f}",
            f"{self.thickness_setpoint:.3f}",
            str(self.time_setpoint),
            str(mask),
        ]