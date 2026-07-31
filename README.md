# SQM160

Python interface for the INFICON SQM-160 deposition monitor.

## Installation

```bash
pip install -e .

```

## Example

```python
from sqm160 import SQM160

with SQM160() as sqm:

    print("Average rate      :", sqm.average_rate())
    print("Average thickness :", sqm.average_thickness())

    print("Sensor 1 rate     :", sqm.sensor_rate(1))
    print("Sensor 1 thickness:", sqm.sensor_thickness(1))

```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
