# SQM160

Python interface for the INFICON SQM-160 deposition monitor.

## Installation

```bash
pip install sqm160

```

## Example

```python
from sqm160 import SQM160

with SQM160() as sqm:
    print(sqm.firmware_version())

```

## License

This project is licensed under the MIT License. See the LICENSE file for details.