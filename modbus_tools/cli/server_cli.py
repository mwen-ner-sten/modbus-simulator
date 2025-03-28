#!/usr/bin/env python
"""
server_cli.py - Simple CLI Modbus TCP server
"""

import logging
import argparse
import json
import os
import sys
import time
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

def load_registers_from_file(filename):
    """Load register values from a JSON file"""
    try:
        if not os.path.exists(filename):
            logger.error(f"File not found: {filename}")
            return None
            
        with open(filename, 'r') as f:
            data = json.load(f)
            
        # Convert string keys to integers
        registers = {}
        for reg_type in ["hr", "ir", "co", "di"]:
            if reg_type in data:
                registers[reg_type] = {int(k): v for k, v in data[reg_type].items()}
                logger.info(f"Loaded {len(registers[reg_type])} {reg_type} registers")
            else:
                registers[reg_type] = {}
                
        return registers
    except Exception as e:
        logger.error(f"Error loading registers: {str(e)}")
        return None

def create_context(registers=None):
    """Create a Modbus server context with the specified register values"""
    
    # Default register values if none provided
    if registers is None:
        logger.info("Using default register values")
        # Create default register values
        hr_values = [0] * 10
        ir_values = [100] * 10
        co_values = [True] * 10
        di_values = [False] * 10
    else:
        logger.info("Using provided register values")
        
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
    
    # Log the register values
    logger.info("Register values:")
    logger.info(f"HR: {hr_values}")
    logger.info(f"IR: {ir_values}")
    logger.info(f"CO: {co_values}")
    logger.info(f"DI: {di_values}")
    
    # Create data blocks
    holding_registers = ModbusSequentialDataBlock(0, hr_values)
    input_registers = ModbusSequentialDataBlock(0, ir_values)
    coils = ModbusSequentialDataBlock(0, co_values)
    discrete_inputs = ModbusSequentialDataBlock(0, di_values)
    
    # Create slave context
    slave_context = ModbusSlaveContext(
        di=discrete_inputs,    # Discrete Inputs
        co=coils,             # Coils
        hr=holding_registers, # Holding Registers
        ir=input_registers,   # Input Registers
        zero_mode=True        # Use zero-based addressing
    )
    
    # Create server context
    return ModbusServerContext(slaves=slave_context, single=True)

async def run_server(context, host="127.0.0.1", port=502):
    """Run the Modbus TCP server"""
    logger.info(f"Starting Modbus TCP server on {host}:{port}")
    
    # Verify registers before starting server
    slave_context = context[0]
    logger.info("Initial register values in server context:")
    try:
        logger.info(f"HR[0:10]: {slave_context.getValues(3, 0, 10)}")  # 3 = hr
        logger.info(f"IR[0:10]: {slave_context.getValues(4, 0, 10)}")  # 4 = ir
        logger.info(f"CO[0:10]: {slave_context.getValues(1, 0, 10)}")  # 1 = co
        logger.info(f"DI[0:10]: {slave_context.getValues(2, 0, 10)}")  # 2 = di
    except:
        logger.warning("Error retrieving register values, using default range")
        logger.info(f"HR[0:5]: {slave_context.getValues(3, 0, 5)}")  # 3 = hr
        logger.info(f"IR[0:5]: {slave_context.getValues(4, 0, 5)}")  # 4 = ir
        logger.info(f"CO[0:5]: {slave_context.getValues(1, 0, 5)}")  # 1 = co
        logger.info(f"DI[0:5]: {slave_context.getValues(2, 0, 5)}")  # 2 = di
    
    try:
        # Start server
        await StartTcpServer(
            context=context,
            address=(host, port),
            allow_reuse_address=True
        )
        
        logger.info(f"Server started on {host}:{port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error running server: {str(e)}")
        sys.exit(1)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Simple Modbus TCP Server')
    parser.add_argument('--host', type=str, default="127.0.0.1",
                        help='Host address to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=502,
                        help='TCP port to listen on (default: 502)')
    parser.add_argument('--file', type=str, default="registers.json",
                        help='JSON file containing register values (default: registers.json)')
    parser.add_argument('--loglevel', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set logging level (default: INFO)')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.loglevel))
    
    # Load registers from file
    registers = load_registers_from_file(args.file)
    
    # Create server context
    context = create_context(registers)
    
    # Run server
    try:
        asyncio.run(run_server(context, args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 