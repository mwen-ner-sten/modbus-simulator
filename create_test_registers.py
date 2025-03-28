#!/usr/bin/env python
"""
create_test_registers.py - Create a test registers.json file
"""

import json
import os
import sys

def create_test_registers():
    """Create a test registers.json file with non-zero values"""
    registers = {
        "hr": {  # Holding registers
            "0": 12345,
            "1": 54321,
            "2": 9999,
            "3": 8888,
            "4": 7777,
            "5": 6666,
            "6": 5555,
            "7": 4444,
            "8": 3333,
            "9": 2222
        },
        "ir": {  # Input registers
            "0": 5000,
            "1": 5001,
            "2": 5002,
            "3": 5003,
            "4": 5004,
            "5": 5005,
            "6": 5006,
            "7": 5007,
            "8": 5008,
            "9": 5009
        },
        "co": {  # Coils
            "0": True,
            "1": False,
            "2": True,
            "3": False,
            "4": True,
            "5": False,
            "6": True,
            "7": False,
            "8": True,
            "9": False
        },
        "di": {  # Discrete inputs
            "0": True,
            "1": True,
            "2": False,
            "3": False,
            "4": True,
            "5": True,
            "6": False,
            "7": False,
            "8": True,
            "9": False
        }
    }
    
    # Write to file
    with open("test_registers.json", "w") as f:
        json.dump(registers, f, indent=4)
        
    print(f"Created test_registers.json with test values")
    print("You can now run the server with:")
    print("python server_cli.py --file test_registers.json")
    print("\nAnd then read values with:")
    print("python client_cli.py --function hr --address 0 --count 5")

if __name__ == "__main__":
    create_test_registers() 