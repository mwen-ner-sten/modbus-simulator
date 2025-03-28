"""
context.py - Custom Modbus server context to handle various error behaviors
"""

import logging
from typing import Dict, Any, Callable, Optional
from pymodbus.datastore import ModbusServerContext, ModbusSparseDataBlock
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus.constants import Endian
from pymodbus.interfaces import IModbusSlaveContext


class CustomModbusSparseDataBlock(ModbusSparseDataBlock):
    """
    A custom Modbus sparse data block that supports various error behaviors
    """

    def __init__(self, values, error_map=None):
        """
        Initialize the custom data block

        Args:
            values: Initial values dictionary
            error_map: Dictionary mapping addresses to error behaviors
        """
        super().__init__(values)
        self.error_map = error_map or {}

    def getValues(self, address, count=1):
        """
        Get values from the datastore

        This method is overridden to implement custom error behaviors.

        Args:
            address: The starting address
            count: The number of values to retrieve

        Returns:
            The requested values

        Raises:
            ModbusException: If an error behavior is triggered
        """
        # Check for error behaviors for each address in the range
        for addr in range(address, address + count):
            if addr in self.error_map:
                error_behavior = self.error_map[addr]

                # Handle different error behaviors
                if error_behavior == "ERROR_ILLEGAL_FUNCTION":
                    raise ModbusException(1)  # Illegal function
                elif error_behavior == "ERROR_ILLEGAL_ADDRESS":
                    raise ModbusException(2)  # Illegal address
                elif error_behavior == "ERROR_ILLEGAL_VALUE":
                    raise ModbusException(3)  # Illegal value
                elif error_behavior == "ERROR_SERVER_FAILURE":
                    raise ModbusException(4)  # Server failure
                elif error_behavior == "ERROR_ACKNOWLEDGE":
                    raise ModbusException(5)  # Acknowledge
                elif error_behavior == "ERROR_SERVER_BUSY":
                    raise ModbusException(6)  # Server busy
                elif error_behavior == "ERROR_MEMORY_PARITY":
                    raise ModbusException(8)  # Memory parity error
                elif error_behavior == "ERROR_GATEWAY_PATH":
                    raise ModbusException(10)  # Gateway path unavailable
                elif error_behavior == "ERROR_GATEWAY_TARGET":
                    raise ModbusException(11)  # Gateway target failed to respond
                elif error_behavior == "NO_RESPONSE":
                    logging.debug(f"Address {addr} is set to NO_RESPONSE, delaying...")
                    import time

                    time.sleep(60)  # Simulate no response by waiting for a long time

                # Other behaviors like RETURN_ZERO, RETURN_MAX_UINT, etc. are handled
                # by setting the appropriate values in the setValues method

        # If no error was triggered, return values normally
        return super().getValues(address, count)

    def setValues(self, address, values):
        """
        Set values in the datastore

        This method is overridden to implement custom error behaviors.

        Args:
            address: The starting address
            values: The values to set

        Returns:
            None

        Raises:
            ModbusException: If an error behavior is triggered
        """
        # Check for error behaviors for each address in the range
        for i, addr in enumerate(range(address, address + len(values))):
            if addr in self.error_map:
                error_behavior = self.error_map[addr]

                # Handle different error behaviors
                if error_behavior in [
                    "ERROR_ILLEGAL_FUNCTION",
                    "ERROR_ILLEGAL_ADDRESS",
                    "ERROR_ILLEGAL_VALUE",
                    "ERROR_SERVER_FAILURE",
                    "ERROR_ACKNOWLEDGE",
                    "ERROR_SERVER_BUSY",
                    "ERROR_MEMORY_PARITY",
                    "ERROR_GATEWAY_PATH",
                    "ERROR_GATEWAY_TARGET",
                ]:
                    # These are handled in getValues
                    pass
                elif error_behavior == "RETURN_ZERO":
                    values[i] = 0
                elif error_behavior == "RETURN_MAX_UINT":
                    values[i] = 0xFFFF
                elif error_behavior == "RETURN_MAX_INT":
                    values[i] = 0x7FFF

        # Call the parent method to set the values
        super().setValues(address, values)


class CustomModbusSlaveContext:
    """
    A custom Modbus slave context that uses our custom data blocks
    """

    def __init__(self, registers, slave_id):
        """
        Initialize the custom slave context

        Args:
            registers: Dictionary of ModbusRegister objects
            slave_id: The slave ID
        """
        self.registers = registers
        self.slave_id = slave_id

        # Initialize data blocks for each register type
        self.coils = self._create_data_block("COIL")
        self.discrete_inputs = self._create_data_block("DISCRETE_INPUT")
        self.input_registers = self._create_data_block("INPUT_REGISTER")
        self.holding_registers = self._create_data_block("HOLDING_REGISTER")

    def _create_data_block(self, register_type):
        """
        Create a data block for a specific register type

        Args:
            register_type: The register type

        Returns:
            CustomModbusSparseDataBlock: The data block
        """
        values = {}
        error_map = {}

        for address, register in self.registers.items():
            if register.register_type == register_type:
                values[address] = register.value

                if not register.enabled or register.error_behavior != "NORMAL":
                    error_map[address] = register.error_behavior

        return CustomModbusSparseDataBlock(values, error_map)


def create_custom_modbus_context(registers, slave_id=1):
    """
    Create a custom Modbus server context

    Args:
        registers: Dictionary of ModbusRegister objects
        slave_id: The slave ID

    Returns:
        ModbusServerContext: The server context
    """
    # Create slave context
    slaves = {slave_id: CustomModbusSlaveContext(registers, slave_id)}

    # Create server context
    context = ModbusServerContext(slaves=slaves, single=False)

    return context
