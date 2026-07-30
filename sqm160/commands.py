"""
High-level SQM-160 commands.

Every method corresponds to one command described in
Chapter 8.4 of the SQM-160 Operating Manual.
"""

from __future__ import annotations

from .models import SensorMeasurement, SystemParameters, SystemParameters2, FilmParameters


class SQM160Commands:
    """
    High-level command interface for the SQM-160.
    """

    def _check_range(
        self,
        value: int,
        minimum: int,
        maximum: int,
        name: str,
    ) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(
                f"{name} must be between {minimum} and {maximum}."
            )

    def _check_sensor(self, sensor: int) -> None:
        self._check_range(sensor, 1, 6, "Sensor number")



    def _check_film(self, sensor: int) -> None:
        self._check_range(sensor, 1, 99, "Film number")


    # ---------------------------------------------------------
    # System information
    # ---------------------------------------------------------

    
    def firmware_version(self) -> str:
        """
        Return the firmware version.

        Manual command:
            @

        Returns
        -------
        str
            Firmware version string, e.g.

            "MON Ver 4.13"
        """

        return self.query_string("@")

        
    
    def channel_count(self) -> int:
        """
        Return the number of installed measurement channels.

        Manual command:
            J

        Returns
        -------
        int
            Number of installed channels (2 or 6).
        """

        return self.query_int("J")



    def power_up_reset(self) -> bool:
        """
        Return the status of the Power-Up Reset flag.
    
        The flag is set after the SQM-160 powers up and is cleared
        automatically after it is read once.
    
        Manual command:
            Y
    
        Returns
        -------
        bool
            True if the Power-Up Reset flag is set.
            False otherwise.
        """
    
        return self.query_bool("Y")
    

    # ---------------------------------------------------------
    # Sensor measurements
    # ---------------------------------------------------------

    def sensor_rate(self, sensor: int) -> float:
        """
        Return the current deposition rate measured by a sensor.

        Manual command:
            L

        Parameters
        ----------
        sensor : int
            Sensor number (1–6).

        Returns
        -------
        float
            Current deposition rate.
        """

        self._check_sensor(sensor)
        return self.query_float(f"L{sensor}")

    # ---------------------------------------------------------

    def sensor_thickness(self, sensor: int) -> float:
        """
        Return the accumulated thickness measured by a sensor.

        Manual command:
            N

        Parameters
        ----------
        sensor : int
            Sensor number (1–6).

        Returns
        -------
        float
            Current thickness.
        """

        self._check_sensor(sensor)
        return self.query_float(f"N{sensor}")

    # ---------------------------------------------------------

    def sensor_frequency(self, sensor: int) -> float:
        """
        Return the current crystal frequency.

        Manual command:
            P

        Parameters
        ----------
        sensor : int
            Sensor number (1–6).

        Returns
        -------
        float
            Crystal frequency (Hz).
        """

        self._check_sensor(sensor)
        return self.query_float(f"P{sensor}")

    # ---------------------------------------------------------

    def sensor_life(self, sensor: int) -> float:
        """
        Return the remaining crystal life.

        Manual command:
            R

        Parameters
        ----------
        sensor : int
            Sensor number (1–6).

        Returns
        -------
        float
            Remaining crystal life (percent).
        """

        self._check_sensor(sensor)
        return self.query_float(f"R{sensor}")

    # ---------------------------------------------------------

    def sensor_measurements(self) -> dict[int, SensorMeasurement]:
        """
        Read the current rate, thickness and frequency of all sensors.
    
        Manual command:
            W
        """
    
        return SensorMeasurement.parse_measurements(
            self.query_fields("W")
        )
        

    # ---------------------------------------------------------
    # Averaged measurements
    # ---------------------------------------------------------

    def average_rate(self) -> float:
        """
        Return the current average deposition rate.

        Manual command:
            M

        Returns
        -------
        float
            Average deposition rate.
        """

        return self.query_float("M")

    # ---------------------------------------------------------

    def average_thickness(self) -> float:
        """
        Return the current average accumulated thickness.

        Manual command:
            O

        Returns
        -------
        float
            Average accumulated thickness.
        """

        return self.query_float("O")





    # ---------------------------------------------------------
    # Reset commands
    # ---------------------------------------------------------

    def reset_measurement(self) -> None:
        """
        Reset the average accumulated thickness and rate to zero.

        Manual command:
            S
        """

        self.query("S")

    # ---------------------------------------------------------

    def reset_time(self) -> None:
        """
        Reset the elapsed deposition timer.

        Manual command:
            T
        """

        self.query("T")


    def restore_defaults(self) -> None:
        """
        Restore all film and system parameters to their factory defaults.
    
        Manual command:
            Z
        """
    
        self.query("Z")

    # ---------------------------------------------------------
    # Shutter commands
    # ---------------------------------------------------------


    def shutter_status(self) -> bool:
        """
        Return True if the source shutter is open.
        """
    
        return self.query_bool("U?")



    def open_shutter(self) -> None:
        """
        Open the source shutter.
    
        Manual command:
            U1
        """
    
        self.query("U1")


    def close_shutter(self) -> None:
        """
        Close the source shutter.
    
        Manual command:
            U0
        """
    
        self.query("U0")



    # ---------------------------------------------------------
    # Film commands
    # ---------------------------------------------------------

    def select_film(self, film: int) -> None:
        """
        Select the active film.

        Manual command:
            D

        Parameters
        ----------
        film : int
            Film number (1–99).
        """

        self._check_film(film)
        self.query(f"D{film}")


    def film_parameters(
        self,
        film_number: int,
    ) -> FilmParameters:
        """
        Read film parameters.
    
        Manual command:
            A
        """
    
        self._check_range(film_number, 1, 99, "Film number")
    
        return FilmParameters.parse(
            film_number,
            self.query_string(f"A{film_number}?"),
        )


    def set_film_parameters(
        self,
        film_parameters: FilmParameters,
    ) -> None:
        """
        Update film parameters.
    
        Manual command:
            A
        """
    
        self.query(
            f"A{film_parameters.film_number}"
            + " ".join(film_parameters.serialize())
        )


    # ---------------------------------------------------------
    # System settings commands
    # ---------------------------------------------------------
    
    def system_parameters(self) -> SystemParameters:
        """
        Read the System 1 parameters.
    
        Manual command:
            B?
    
        Returns
        -------
        SystemParameters
            Current System 1 parameters.
        """
    
        return SystemParameters.parse(
            self.query_fields("B?")
        )
    
    
    # ---------------------------------------------------------
    
    def set_system_parameters(
        self,
        parameters: SystemParameters,
    ) -> None:
        """
        Update the System 1 parameters.
    
        Manual command:
            B
    
        Parameters
        ----------
        parameters
            New System 1 parameters.
        """
    
        command = "B " + " ".join(
            parameters.serialize()
        )
    
        self.query(command)



    
    def system_parameters2(self) -> SystemParameters2:
        """
        Read System 2 parameters.
    
        Manual command:
            C?
        """
    
        return SystemParameters2.parse(
            self.query_fields("C?")
        )

    
    def set_system_parameters2(
        self,
        parameters: SystemParameters2,
    ) -> None:
        """
        Update System 2 parameters.
    
        Manual command:
            C
        """
    
        command = "C " + " ".join(
            parameters.serialize()
        )
    
        self.query(command)