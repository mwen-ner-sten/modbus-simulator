#!/usr/bin/env python
"""
client_cli.py - Simple CLI Modbus TCP client
"""

import logging
import argparse
import sys
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

def read_registers(host, port, unit, function, address, count):
    """Read registers from a Modbus server"""
    logger.info(f"Connecting to Modbus server at {host}:{port}")
    logger.info(f"Reading {function} at address {address}, count {count}, unit {unit}")
    
    # Create a client connection
    client = ModbusTcpClient(host, port=port)
    
    try:
        # Connect to the server
        connection = client.connect()
        if not connection:
            logger.error("Failed to connect to server")
            return False
            
        logger.info("Connected to server")
        
        # Select the appropriate read function
        if function == "hr":
            logger.info("Reading holding registers")
            result = client.read_holding_registers(address, count, unit=unit)
        elif function == "ir":
            logger.info("Reading input registers")
            result = client.read_input_registers(address, count, unit=unit)
        elif function == "co":
            logger.info("Reading coils")
            result = client.read_coils(address, count, unit=unit)
        elif function == "di":
            logger.info("Reading discrete inputs")
            result = client.read_discrete_inputs(address, count, unit=unit)
        else:
            logger.error(f"Unknown function code: {function}")
            return False
            
        # Check if we got a valid result
        if not result or result.isError():
            logger.error(f"Error reading registers: {result}")
            return False
            
        # Display the results
        if hasattr(result, 'registers'):
            logger.info(f"Register values: {result.registers}")
            
            # Print in a more readable format
            print("\nRegister Values:")
            print("----------------")
            for i, value in enumerate(result.registers):
                print(f"Address {address+i}: {value}")
        elif hasattr(result, 'bits'):
            logger.info(f"Bit values: {result.bits}")
            
            # Print in a more readable format
            print("\nBit Values:")
            print("-----------")
            for i, value in enumerate(result.bits):
                print(f"Address {address+i}: {value}")
        else:
            logger.info(f"Result: {result}")
            
        return True
        
    except ModbusException as e:
        logger.error(f"Modbus error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        # Close the connection
        client.close()
        logger.info("Connection closed")
        
def write_register(host, port, unit, function, address, value):
    """Write a value to a register on a Modbus server"""
    logger.info(f"Connecting to Modbus server at {host}:{port}")
    logger.info(f"Writing to {function} at address {address}, value {value}, unit {unit}")
    
    # Create a client connection
    client = ModbusTcpClient(host, port=port)
    
    try:
        # Connect to the server
        connection = client.connect()
        if not connection:
            logger.error("Failed to connect to server")
            return False
            
        logger.info("Connected to server")
        
        # Select the appropriate write function
        if function == "hr":
            logger.info("Writing to holding register")
            # Convert value to integer
            int_value = int(value)
            result = client.write_register(address, int_value, unit=unit)
        elif function == "co":
            # Convert value to boolean
            bool_value = bool(int(value))
            logger.info(f"Writing to coil with boolean value {bool_value}")
            result = client.write_coil(address, bool_value, unit=unit)
        else:
            logger.error(f"Cannot write to {function} registers")
            return False
            
        # Check if we got a valid result
        if not result or result.isError():
            logger.error(f"Error writing to register: {result}")
            return False
            
        logger.info(f"Successfully wrote value {value} to {function} at address {address}")
        return True
        
    except ModbusException as e:
        logger.error(f"Modbus error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        # Close the connection
        client.close()
        logger.info("Connection closed")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Simple Modbus TCP Client')
    parser.add_argument('--host', type=str, default="127.0.0.1",
                        help='Host address (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=502,
                        help='TCP port (default: 502)')
    parser.add_argument('--unit', type=int, default=1,
                        help='Unit ID (default: 1)')
    parser.add_argument('--function', type=str, choices=['hr', 'ir', 'co', 'di'],
                        default='hr', help='Function code (hr=holding registers, ir=input registers, co=coils, di=discrete inputs)')
    parser.add_argument('--address', type=int, default=0,
                        help='Starting address (default: 0)')
    parser.add_argument('--count', type=int, default=10,
                        help='Number of registers to read (default: 10)')
    parser.add_argument('--write', type=str, 
                        help='Value to write (if specified, performs a write operation instead of read)')
    parser.add_argument('--loglevel', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set logging level (default: INFO)')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.loglevel))
    
    # Determine operation type (read or write)
    if args.write is not None:
        # Write operation
        success = write_register(
            args.host, args.port, args.unit, args.function, 
            args.address, args.write
        )
    else:
        # Read operation
        success = read_registers(
            args.host, args.port, args.unit, args.function, 
            args.address, args.count
        )
        
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 