"""
server.py - Modbus TCP server implementation
"""

import logging
import argparse
import json
import os
import time
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
import asyncio
import signal
import sys

# Set up logger for this module
logger = logging.getLogger(__name__)

# Global server context
server_context = None
# Global register file
register_file = "registers.json"
# Global last modified time
last_modified_time = 0

def load_registers_from_file():
    """
    Load registers from JSON file
    """
    global last_modified_time
    
    try:
        if os.path.exists(register_file):
            # Update last modified time
            last_modified_time = os.path.getmtime(register_file)
            
            logger.info(f"Loading registers from {register_file}")
            with open(register_file, 'r') as f:
                data = json.load(f)
                
            # Convert string keys to integers
            registers = {}
            for reg_type in ["hr", "ir", "co", "di"]:
                if reg_type in data:
                    registers[reg_type] = {int(k): v for k, v in data[reg_type].items()}
                    logger.info(f"Loaded {len(registers[reg_type])} {reg_type} registers")
                else:
                    # Default empty dict
                    registers[reg_type] = {}
            
            logger.debug(f"Register contents: {registers}")
            return registers
        else:
            logger.warning(f"Register file {register_file} not found, using default values")
            return None
    except Exception as e:
        logger.error(f"Error loading registers from file: {str(e)}", exc_info=True)
        return None

def initialize_server():
    """
    Initialize the Modbus server with data
    """
    logger.debug("Initializing Modbus server")
    
    # Try to load registers from file
    registers = load_registers_from_file()
    
    if not registers:
        # Use default values
        logger.debug("Using default register values")
        # Initialize holding registers (40001-40010) with test values
        hr_values = [0] * 10
        # Initialize input registers (30001-30010) with test values
        ir_values = [100] * 10
        # Initialize coils (00001-00010) with test values
        co_values = [True] * 10
        # Initialize discrete inputs (10001-10010) with test values
        di_values = [False] * 10
    else:
        # Extract values from loaded registers
        logger.debug("Using loaded register values")
        
        # Get the highest address
        hr_max = max(registers["hr"].keys()) + 1 if registers["hr"] else 10
        ir_max = max(registers["ir"].keys()) + 1 if registers["ir"] else 10
        co_max = max(registers["co"].keys()) + 1 if registers["co"] else 10
        di_max = max(registers["di"].keys()) + 1 if registers["di"] else 10
        
        # Create arrays with default values
        hr_values = [0] * hr_max
        ir_values = [0] * ir_max
        co_values = [False] * co_max
        di_values = [False] * di_max
        
        # Fill in the values
        for addr, val in registers["hr"].items():
            if addr < len(hr_values):
                hr_values[addr] = val
                logger.debug(f"Set HR register {addr} to {val}")
                
        for addr, val in registers["ir"].items():
            if addr < len(ir_values):
                ir_values[addr] = val
                logger.debug(f"Set IR register {addr} to {val}")
                
        for addr, val in registers["co"].items():
            if addr < len(co_values):
                co_values[addr] = val
                logger.debug(f"Set CO register {addr} to {val}")
                
        for addr, val in registers["di"].items():
            if addr < len(di_values):
                di_values[addr] = val
                logger.debug(f"Set DI register {addr} to {val}")
    
    logger.info("Register values that will be used:")
    logger.info(f"HR: {hr_values}")
    logger.info(f"IR: {ir_values}")
    logger.info(f"CO: {co_values}")
    logger.info(f"DI: {di_values}")
    
    # Create data blocks
    holding_registers = ModbusSequentialDataBlock(0, hr_values)
    input_registers = ModbusSequentialDataBlock(0, ir_values)
    coils = ModbusSequentialDataBlock(0, co_values)
    discrete_inputs = ModbusSequentialDataBlock(0, di_values)
    
    # Verify the values are set correctly
    logger.info("Verifying register values were set correctly:")
    logger.info(f"HR[0:10]: {holding_registers.getValues(0, min(10, len(hr_values)))}")
    logger.info(f"IR[0:10]: {input_registers.getValues(0, min(10, len(ir_values)))}")
    logger.info(f"CO[0:10]: {coils.getValues(0, min(10, len(co_values)))}")
    logger.info(f"DI[0:10]: {discrete_inputs.getValues(0, min(10, len(di_values)))}")
    
    # Create slave context
    slave_context = ModbusSlaveContext(
        di=discrete_inputs,    # Discrete Inputs
        co=coils,             # Coils
        hr=holding_registers, # Holding Registers
        ir=input_registers,   # Input Registers
        zero_mode=True        # Use zero-based addressing
    )
    
    # Create server context
    global server_context
    server_context = ModbusServerContext(slaves=slave_context, single=True)
    
    logger.info("Server initialized with register data")

async def check_register_changes():
    """
    Check for changes to the register file
    """
    global last_modified_time
    
    while True:
        try:
            # Check if file exists and has been modified
            if os.path.exists(register_file):
                mod_time = os.path.getmtime(register_file)
                if mod_time > last_modified_time:
                    logger.info(f"Register file changed, reloading values")
                    initialize_server()
        except Exception as e:
            logger.error(f"Error checking register changes: {str(e)}", exc_info=True)
            
        # Check every second
        await asyncio.sleep(1)

async def run_server(host="127.0.0.1", port=502):
    """
    Run the Modbus TCP server
    """
    try:
        logger.info(f"Starting Modbus TCP Server on {host}:{port}")
        
        # Initialize server with data
        initialize_server()
        
        # For debugging, dump the initial register values
        slave_context = server_context[0]
        logger.info("Initial register values in server context:")
        logger.info(f"HR[0:10]: {slave_context.getValues(3, 0, 10)}")  # 3 = hr
        logger.info(f"IR[0:10]: {slave_context.getValues(4, 0, 10)}")  # 4 = ir
        logger.info(f"CO[0:10]: {slave_context.getValues(1, 0, 10)}")  # 1 = co
        logger.info(f"DI[0:10]: {slave_context.getValues(2, 0, 10)}")  # 2 = di
        
        # Start server
        await StartTcpServer(
            context=server_context,
            address=(host, port),
            allow_reuse_address=True
        )
        
        logger.info(f"Server started on {host}:{port}")
        
        # Start file watcher
        asyncio.create_task(check_register_changes())
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error running server: {str(e)}", exc_info=True)
        sys.exit(1)

def signal_handler(signum, frame):
    """
    Handle shutdown signals
    """
    logger.info("Received shutdown signal")
    sys.exit(0)

def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Modbus TCP Server')
    parser.add_argument('--host', type=str, default="127.0.0.1",
                        help='Host address to bind to')
    parser.add_argument('--port', type=int, default=502,
                        help='TCP port to listen on')
    parser.add_argument('--register-file', type=str, default="registers.json",
                        help='JSON file containing register values')
    parser.add_argument('--loglevel', type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help='Logging level')
    return parser.parse_args()

def main():
    """
    Main entry point for the server
    """
    # Parse command line arguments
    args = parse_args()
    
    # Set register file
    global register_file
    register_file = args.register_file
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up basic logging
    logging.basicConfig(
        level=getattr(logging, args.loglevel),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the server with the specified host and port
    asyncio.run(run_server(host=args.host, port=args.port))

if __name__ == "__main__":
    main()
