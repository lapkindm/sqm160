# SQM-160 Python Driver

A Python driver for the INFICON SQM-160 Thin Film Deposition Monitor.

The package provides a high-level Python interface to the SQM-160 and
supports communication through both:

- USB
- RS-232

The same SQM-160 command and protocol layer is used for both interfaces.


## Installation

### From source

Clone the repository and install it in editable mode:

```bash
pip install -e .
```

For a regular installation:

```bash
pip install .
```

## Basic usage

The high-level interface is provided by `SQM160`.

```python
from sqm160 import SQM160

with SQM160() as sqm:
    print(sqm.firmware_version())
```

Example output:

```text
MON Ver 4.13
```

The connection is automatically opened when entering the `with` block and
closed when leaving it.

## USB communication

USB is the default transport.

```python
from sqm160 import SQM160

with SQM160() as sqm:
    print(sqm.firmware_version())
```

USB devices can also be selected explicitly using their VID and PID:

```python
from sqm160 import SQM160

with SQM160(
    vid=0x10C4,
    pid=0x83F5,
) as sqm:
    print(sqm.firmware_version())
```

The driver can also identify the SQM-160 using USB descriptors such as the
manufacturer, product name, and serial number.

## RS-232 communication

The SQM-160 can also be accessed through its RS-232 interface.

For development, an RS-232-to-USB adapter appears as a serial device such as
`/dev/ttyUSB1` on Linux.

```python
from sqm160 import SQM160, SerialTransport

transport = SerialTransport(
    port="/dev/ttyUSB1",
)

with SQM160(transport=transport) as sqm:
    print(sqm.firmware_version())
```

The default serial configuration is:


The serial transport uses the same SQM-160 command protocol as the USB
transport.


## Reading measurements

### Sensor measurements

The SQM-160 supports up to six sensors.

```python
from sqm160 import SQM160

with SQM160() as sqm:

    print(sqm.sensor_rate(1))
    print(sqm.sensor_thickness(1))
    print(sqm.sensor_frequency(1))
    print(sqm.sensor_life(1))
```

The sensor number must be between 1 and 6.

### All sensor measurements

The `W` command reads rate, thickness, and frequency for all installed
sensors simultaneously.

```python
from sqm160 import SQM160

with SQM160() as sqm:

    measurements = sqm.sensor_measurements()

    for sensor, measurement in measurements.items():
        print(
            sensor,
            measurement.rate,
            measurement.thickness,
            measurement.frequency,
        )
```

The result is a dictionary containing `SensorMeasurement` objects:

```python
{
    1: SensorMeasurement(
        rate=9.86,
        thickness=218.925,
        frequency=5500035.127,
    ),
    2: SensorMeasurement(
        rate=0.0,
        thickness=0.0,
        frequency=5500220.023,
    ),
    ...
}
```

## Average measurements

The current average deposition rate and thickness can be queried with:

```python
from sqm160 import SQM160

with SQM160() as sqm:

    print("Average rate:", sqm.average_rate())
    print("Average thickness:", sqm.average_thickness())
```

The averages can be reset with:

```python
with SQM160() as sqm:
    sqm.reset_measurement()
```

The elapsed deposition timer can be reset with:

```python
with SQM160() as sqm:
    sqm.reset_time()
```


## Shutter control

The source shutter can be queried and controlled through:

```python
from sqm160 import SQM160

with SQM160() as sqm:

    print(sqm.shutter_status())

    sqm.open_shutter()

    print(sqm.shutter_status())

    sqm.close_shutter()
```

`shutter_status()` returns:

- `True` — shutter open
- `False` — shutter closed

## System parameters

### System parameters 1

System 1 parameters are represented by the `SystemParameters` dataclass.

```python
from sqm160 import SQM160

with SQM160() as sqm:

    parameters = sqm.system_parameters()

    print(parameters)
```

Example:

```text
SystemParameters(
    time_base=0.3,
    simulate_mode=False,
    display_mode=DisplayMode.ANGSTROM,
    high_rate_resolution=False,
    rate_filter=8,
    crystal_tooling=(100, 100, 100, 100, 100, 100),
)
```

Parameters can be modified using `copy()`:

```python
with SQM160() as sqm:

    parameters = sqm.system_parameters()

    parameters = parameters.copy(
        simulate_mode=False,
        rate_filter=10,
    )

    sqm.set_system_parameters(parameters)
```

### System parameters 2

System 2 parameters are represented by `SystemParameters2`.

```python
from sqm160 import SQM160

with SQM160() as sqm:

    parameters = sqm.system_parameters2()

    print(parameters)
```

Example:

```text
SystemParameters2(
    min_frequency=5.0,
    max_frequency=6.0,
    min_rate=0.0,
    max_rate=100.0,
    min_thickness=0.0,
    max_thickness=1.0,
    etch_mode=False,
)
```

They can be modified in the same way:

```python
with SQM160() as sqm:

    parameters = sqm.system_parameters2()

    parameters = parameters.copy(
        max_rate=100.0,
    )

    sqm.set_system_parameters2(parameters)
```

## Film parameters

Film parameters are represented by the `FilmParameters` dataclass.

A film can be queried by its film number:

```python
from sqm160 import SQM160

with SQM160() as sqm:

    film = sqm.film_parameters(1)

    print(film)
```

Example:

```text
FilmParameters(
    film_number=1,
    name='FILM 1',
    density=0.5,
    tooling=100,
    z_ratio=1.0,
    final_thickness=0.5,
    thickness_setpoint=0.0,
    time_setpoint=0,
    active_sensors=(1,),
)
```

Film parameters can be modified using `copy()`:

```python
with SQM160() as sqm:

    film = sqm.film_parameters(1)

    film = film.copy(
        density=1.23,
        tooling=150,
        z_ratio=1.23,
    )

    sqm.set_film_parameters(film)
```

## Power-up reset flag

The SQM-160 provides a power-up reset flag:

```python
from sqm160 import SQM160

with SQM160() as sqm:

    if sqm.power_up_reset():
        print("Controller has just been powered on.")
```

The flag is cleared when it is read.

## Number of installed channels

The number of installed sensor channels can be queried with:

```python
from sqm160 import SQM160

with SQM160() as sqm:
    print(sqm.channel_count())
```

The SQM-160 returns the number of installed channels, typically 2 or 6.

## Low-level commands

The high-level methods are built on top of the SQM-160 command protocol.

A raw command can be sent using:

```python
from sqm160 import SQM160

with SQM160() as sqm:
    response = sqm.query("@")

    print(response.status)
    print(response.message)
```

For debugging or protocol development, the raw response packet can be obtained
with:

```python
with SQM160() as sqm:
    raw = sqm.raw_query("@")

    print(raw.hex(" "))
```

## Supported commands

The following SQM-160 commands are currently implemented:

| Command | Description | Python method |
|---|---|---|
| `@` | Firmware version | `firmware_version()` |
| `B?` / `B_...` | System 1 parameters | `system_parameters()` / `set_system_parameters()` |
| `C?` / `C_...` | System 2 parameters | `system_parameters2()` / `set_system_parameters2()` |
| `A<n>?` / `A<n>...` | Film parameters | `film_parameters()` / `set_film_parameters()` |
| `D<n>` | Update active film | `set_active_film()` |
| `J` | Number of installed channels | `channel_count()` |
| `L<n>` | Sensor deposition rate | `sensor_rate()` |
| `M` | Average deposition rate | `average_rate()` |
| `N<n>` | Sensor thickness | `sensor_thickness()` |
| `O<n>` | Sensor frequency | `sensor_frequency()` |
| `O` | Average thickness | `average_thickness()` |
| `P<n>` | Sensor crystal life | `sensor_life()` |
| `S` | Reset average measurements | `reset_measurement()` |
| `T` | Reset elapsed time | `reset_time()` |
| `U?` | Shutter status | `shutter_status()` |
| `U0` | Close shutter | `close_shutter()` |
| `U1` | Open shutter | `open_shutter()` |
| `W` | All sensor measurements | `sensor_measurements()` |
| `Y` | Power-up reset flag | `power_up_reset()` |
| `Z` | Reset film and system parameters | `reset()` / command-specific interface |

Some commands described by the SQM-160 manual are intentionally not exposed
as high-level convenience methods yet.


## Status

This project is under active development.

The driver has been tested with an INFICON SQM-160 using:

- USB communication
- RS-232 communication through an RS-232-to-USB adapter

The high-level API currently covers the principal measurement, film,
system-parameter, shutter, and control commands.


## License

This project is distributed under the terms of the license contained in
`LICENSE`.
