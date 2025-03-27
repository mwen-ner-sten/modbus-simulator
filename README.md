# Modbus Tools

A Python-based Modbus toolkit that provides a graphical user interface for simulating Modbus TCP/RTU devices and scanning Modbus networks. This tool allows you to create, configure, and simulate various Modbus registers with different data types and error behaviors, as well as scan and discover Modbus devices on your network.

## Features

- Graphical user interface for easy configuration
- Support for multiple register types (Coils, Discrete Inputs, Input Registers, Holding Registers)
- Various data types (UINT16, INT16, UINT32, INT32, FLOAT32, UINT64, INT64, FLOAT64, STRING, BOOLEAN)
- Configurable error behaviors for testing error handling
- Support for scaling factors and offsets
- Configurable byte and word order
- Import/Export functionality for register configurations
- Real-time register value updates
- TCP and RTU (Serial) communication support
- Network scanning capabilities
- Device discovery tools

## Requirements

- Python 3.6 or higher
- PyQt5
- pymodbus

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mwen-ner-sten/modbus-tools.git
cd modbus-tools
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the simulator:
```bash
python main.py
```

## Configuration

The simulator can be configured through the graphical interface:
1. Add registers with specific addresses and data types
2. Configure error behaviors for testing
3. Set up scaling factors and offsets
4. Configure communication settings (TCP/RTU)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 