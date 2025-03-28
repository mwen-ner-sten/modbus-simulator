"""
models.py - Data models for the Modbus simulator
"""

import json
import csv
from typing import Dict, Any, List, Optional, Union
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSparseDataBlock,
)
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder

# Import our custom context
from context import create_custom_modbus_context

# Define data types
DATA_TYPES = {
    "UINT16": {"size": 1, "signed": False},
    "INT16": {"size": 1, "signed": True},
    "UINT32": {"size": 2, "signed": False},
    "INT32": {"size": 2, "signed": True},
    "FLOAT32": {"size": 2, "signed": True, "float": True},
    "UINT64": {"size": 4, "signed": False},
    "INT64": {"size": 4, "signed": True},
    "FLOAT64": {"size": 4, "signed": True, "float": True},
    "STRING": {"size": 1, "string": True},  # Size per character
    "BOOLEAN": {"size": 1, "bits": True},
}

# Define register types
REGISTER_TYPES = {
    "COIL": 1,
    "DISCRETE_INPUT": 2,
    "INPUT_REGISTER": 3,
    "HOLDING_REGISTER": 4,
}

# Define error behaviors
ERROR_BEHAVIORS = {
    "NORMAL": "Normal response",
    "ERROR_ILLEGAL_FUNCTION": "Illegal function error",
    "ERROR_ILLEGAL_ADDRESS": "Illegal address error",
    "ERROR_ILLEGAL_VALUE": "Illegal value error",
    "ERROR_SERVER_FAILURE": "Server failure error",
    "ERROR_ACKNOWLEDGE": "Acknowledge",
    "ERROR_SERVER_BUSY": "Server busy",
    "ERROR_MEMORY_PARITY": "Memory parity error",
    "ERROR_GATEWAY_PATH": "Gateway path unavailable",
    "ERROR_GATEWAY_TARGET": "Gateway target failed to respond",
    "RETURN_ZERO": "Return 0",
    "RETURN_MAX_UINT": "Return 0xFFFF",
    "RETURN_MAX_INT": "Return 0x7FFF",
    "NO_RESPONSE": "No response",
}


class ModbusRegister:
    """
    Represents a Modbus register with all its properties and configuration
    """

    def __init__(
        self,
        address: int,
        name: str = "",
        value: Union[int, float, bool, str] = 0,
        data_type: str = "UINT16",
        register_type: str = "HOLDING_REGISTER",
        enabled: bool = True,
        error_behavior: str = "NORMAL",
        description: str = "",
    ):
        self.address = address
        self.name = name
        self.value = value
        self.data_type = data_type
        self.register_type = register_type
        self.enabled = enabled
        self.error_behavior = error_behavior
        self.description = description
        self.scaling_factor = 1.0
        self.offset = 0.0
        self.unit = ""
        self.word_order = "BIG"  # BIG or LITTLE
        self.byte_order = "BIG"  # BIG or LITTLE

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert register to dictionary for serialization
        """
        return {
            "address": self.address,
            "name": self.name,
            "value": self.value,
            "data_type": self.data_type,
            "register_type": self.register_type,
            "enabled": self.enabled,
            "error_behavior": self.error_behavior,
            "description": self.description,
            "scaling_factor": self.scaling_factor,
            "offset": self.offset,
            "unit": self.unit,
            "word_order": self.word_order,
            "byte_order": self.byte_order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModbusRegister":
        """
        Create register from dictionary
        """
        register = cls(
            data["address"],
            data["name"],
            data["value"],
            data["data_type"],
            data["register_type"],
            data["enabled"],
            data["error_behavior"],
            data["description"],
        )
        register.scaling_factor = data.get("scaling_factor", 1.0)
        register.offset = data.get("offset", 0.0)
        register.unit = data.get("unit", "")
        register.word_order = data.get("word_order", "BIG")
        register.byte_order = data.get("byte_order", "BIG")
        return register


class ModbusDataStore:
    """
    Manages a collection of Modbus registers and provides the datastore for the Modbus server
    """

    def __init__(self):
        self.registers: Dict[int, ModbusRegister] = {}
        self.context = None
        self.slave_id = 1

    def add_register(self, register: ModbusRegister) -> None:
        """
        Add a register to the datastore
        """
        if register.address not in self.registers:
            self.registers[register.address] = register

    def remove_register(self, address: int) -> None:
        """
        Remove a register from the datastore
        """
        if address in self.registers:
            del self.registers[address]

    def get_register(self, address: int) -> Optional[ModbusRegister]:
        """
        Get a register by address
        """
        return self.registers.get(address)

    def get_all_registers(self) -> List[ModbusRegister]:
        """
        Get all registers
        """
        return list(self.registers.values())

    def get_registers_by_type(self, register_type: str) -> List[ModbusRegister]:
        """
        Get registers by type
        """
        return [
            reg for reg in self.registers.values() if reg.register_type == register_type
        ]

    def encode_value(self, register: ModbusRegister):
        """
        Encode a register value according to its data type and configuration
        """
        builder = BinaryPayloadBuilder(
            byteorder=Endian.Big if register.byte_order == "BIG" else Endian.Little,
            wordorder=Endian.Big if register.word_order == "BIG" else Endian.Little,
        )

        data_type = register.data_type
        value = register.value

        if not register.enabled:
            if register.error_behavior == "RETURN_ZERO":
                value = 0
            elif register.error_behavior == "RETURN_MAX_UINT":
                value = 0xFFFF
            elif register.error_behavior == "RETURN_MAX_INT":
                value = 0x7FFF

        # Apply scaling and offset for numerical values
        if data_type not in ["BOOLEAN", "STRING"]:
            value = (float(value) - register.offset) / register.scaling_factor

        if data_type == "UINT16":
            builder.add_16bit_uint(int(value))
        elif data_type == "INT16":
            builder.add_16bit_int(int(value))
        elif data_type == "UINT32":
            builder.add_32bit_uint(int(value))
        elif data_type == "INT32":
            builder.add_32bit_int(int(value))
        elif data_type == "FLOAT32":
            builder.add_32bit_float(float(value))
        elif data_type == "UINT64":
            builder.add_64bit_uint(int(value))
        elif data_type == "INT64":
            builder.add_64bit_int(int(value))
        elif data_type == "FLOAT64":
            builder.add_64bit_float(float(value))
        elif data_type == "STRING":
            builder.add_string(str(value))
        elif data_type == "BOOLEAN":
            builder.add_bits(bool(value))

        return builder.build()

    def create_context(self) -> ModbusServerContext:
        """
        Create the Modbus server context from the current registers
        """
        # Use our custom context creator
        self.context = create_custom_modbus_context(self.registers, self.slave_id)
        return self.context

    def save_to_file(self, filename: str) -> None:
        """
        Save registers to a JSON file
        """
        data = {"registers": [reg.to_dict() for reg in self.registers.values()]}
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def load_from_file(self, filename: str) -> None:
        """
        Load registers from a JSON file
        """
        with open(filename, "r") as f:
            data = json.load(f)
        self.registers = {}
        for reg_data in data["registers"]:
            register = ModbusRegister.from_dict(reg_data)
            self.registers[register.address] = register

    def export_to_csv(self, filename: str) -> None:
        """
        Export registers to a CSV file
        """
        with open(filename, "w", newline="") as csvfile:
            fieldnames = [
                "address",
                "name",
                "value",
                "data_type",
                "register_type",
                "enabled",
                "error_behavior",
                "description",
                "scaling_factor",
                "offset",
                "unit",
                "word_order",
                "byte_order",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for register in self.registers.values():
                writer.writerow(register.to_dict())

    def import_from_csv(self, filename: str) -> None:
        """
        Import registers from a CSV file
        """
        with open(filename, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            self.registers = {}
            for row in reader:
                # Convert string values to appropriate types
                row["address"] = int(row["address"])
                row["value"] = (
                    float(row["value"]) if "." in row["value"] else int(row["value"])
                )
                row["enabled"] = row["enabled"].lower() == "true"
                row["scaling_factor"] = float(row["scaling_factor"])
                row["offset"] = float(row["offset"])
                register = ModbusRegister.from_dict(row)
                self.registers[register.address] = register
