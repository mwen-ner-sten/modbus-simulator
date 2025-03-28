# Modbus Simulator

This project provides tools for simulating and testing Modbus TCP devices, including both a GUI application and CLI tools.

## Installation

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## GUI Application

The GUI application includes a Modbus simulator and scanner:

```
python main.py
```

### Simulator Tab

- Configure server settings (host, port, register file)
- Manage register values for different register types:
  - Holding Registers (HR)
  - Input Registers (IR)
  - Coils (CO)
  - Discrete Inputs (DI)
- Add, edit, and remove registers
- Save and load register configurations
- Start/stop the Modbus server

### Scanner Tab

- Configure connection settings (host, port, unit ID)
- Select function code (HR, IR, CO, DI)
- Specify register address and count
- Read values from a Modbus device

## CLI Tools

The CLI tools provide a simpler, more direct way to test Modbus functionality:

### Create Test Registers

Create a JSON file with test register values:

```
python create_test_registers.py
```

### Server CLI

Run a Modbus TCP server with register values from a file:

```
python server_cli.py --file test_registers.json --port 502
```

Options:
- `--host`: Host address to bind to (default: 127.0.0.1)
- `--port`: TCP port to listen on (default: 502)
- `--file`: JSON file containing register values (default: registers.json)
- `--loglevel`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Client CLI

Read registers from a Modbus server:

```
python client_cli.py --function hr --address 0 --count 5
```

Options:
- `--host`: Host address (default: 127.0.0.1)
- `--port`: TCP port (default: 502)
- `--unit`: Unit ID (default: 1)
- `--function`: Function code (hr, ir, co, di)
- `--address`: Starting address (default: 0)
- `--count`: Number of registers to read (default: 10)
- `--write`: Value to write (if specified, performs a write operation)
- `--loglevel`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Run Full Test

Execute a complete test sequence:

```
python test_modbus.py
```

This will:
1. Create test register values
2. Start a Modbus server
3. Read registers from the server
4. Write a value and read it back
5. Stop the server

## Register File Format

Register values are stored in JSON format:

```json
{
  "hr": {  
    "0": 12345,
    "1": 54321
  },
  "ir": {  
    "0": 5000,
    "1": 5001
  },
  "co": {  
    "0": true,
    "1": false
  },
  "di": {  
    "0": true,
    "1": true
  }
}
```

Where:
- `hr`: Holding registers (Function Code 3)
- `ir`: Input registers (Function Code 4)
- `co`: Coils (Function Code 1)
- `di`: Discrete inputs (Function Code 2)

## Troubleshooting

- If you encounter port conflicts, try using a different port number.
- Make sure to activate the virtual environment before running any command.
- Check the logs for detailed error information.
- Ensure the Modbus server is running before attempting to read/write registers.
- If writing to registers fails, verify that you're using the correct function code (only HR and CO are writable). 