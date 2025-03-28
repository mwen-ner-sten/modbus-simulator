#!/usr/bin/env python
"""
test_modbus.py - Run a complete test of the Modbus server and client
"""

import os
import sys
import subprocess
import time
import signal
import json

def print_header(text):
    """Print a nicely formatted header"""
    print("\n" + "=" * 70)
    print(f" {text} ".center(70, "="))
    print("=" * 70 + "\n")

def create_test_registers():
    """Create test registers JSON file"""
    print_header("Creating Test Registers")
    
    registers = {
        "hr": {  # Holding registers
            "0": 12345,
            "1": 54321,
            "2": 9999,
            "3": 8888,
            "4": 7777
        },
        "ir": {  # Input registers
            "0": 5000,
            "1": 5001,
            "2": 5002,
            "3": 5003,
            "4": 5004
        },
        "co": {  # Coils
            "0": True,
            "1": False,
            "2": True,
            "3": False,
            "4": True
        },
        "di": {  # Discrete inputs
            "0": True,
            "1": True,
            "2": False,
            "3": False,
            "4": True
        }
    }
    
    # Write to file
    with open("test_registers.json", "w") as f:
        json.dump(registers, f, indent=4)
        
    print("Created test_registers.json with the following values:")
    print(json.dumps(registers, indent=2))
    
    return registers

def run_server(port=5502):
    """Start the Modbus server in a separate process"""
    print_header(f"Starting Modbus Server on port {port}")
    
    # Run the server in a new process
    server_process = subprocess.Popen(
        [
            sys.executable, 
            "server_cli.py", 
            "--port", str(port),
            "--file", "test_registers.json",
            "--loglevel", "INFO"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Give the server some time to start
    time.sleep(2)
    
    print(f"Server started with PID: {server_process.pid}")
    return server_process

def read_registers(port=5502):
    """Read values from the Modbus server"""
    print_header("Reading Registers from Server")
    
    function_codes = [
        ("hr", "Holding Registers"),
        ("ir", "Input Registers"),
        ("co", "Coils"),
        ("di", "Discrete Inputs")
    ]
    
    for code, name in function_codes:
        print(f"\nReading {name} (function code: {code})\n{'-' * 40}")
        
        try:
            # Run the client and capture output
            result = subprocess.run(
                [
                    sys.executable, 
                    "client_cli.py", 
                    "--port", str(port),
                    "--function", code,
                    "--address", "0",
                    "--count", "5",
                    "--loglevel", "INFO"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Print client output
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"Error reading {name}: {e}")
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")

def stop_server(server_process):
    """Stop the Modbus server"""
    print_header("Stopping Modbus Server")
    
    if server_process.poll() is None:
        # Server is still running, terminate it
        print(f"Sending terminate signal to server (PID: {server_process.pid})")
        server_process.terminate()
        
        # Wait for termination
        try:
            server_process.wait(timeout=5)
            print("Server stopped successfully")
        except subprocess.TimeoutExpired:
            print("Server did not respond to terminate signal, sending kill signal")
            server_process.kill()
            server_process.wait()
            print("Server killed")
    else:
        print(f"Server already stopped with return code: {server_process.returncode}")

def run_full_test():
    """Run the complete test sequence"""
    try:
        # Use a non-standard port to avoid conflicts
        port = 5502
        
        # Step 1: Create test registers
        registers = create_test_registers()
        
        # Step 2: Start the server
        server_process = run_server(port)
        
        # Step 3: Read registers
        read_registers(port)
        
        # Step 4: Write a value and read it back
        print_header("Writing and Reading Back a Value")
        
        # Write value 9876 to holding register 0
        print("Writing value 9876 to holding register 0...")
        try:
            write_result = subprocess.run(
                [
                    sys.executable, 
                    "client_cli.py", 
                    "--port", str(port),
                    "--function", "hr",
                    "--address", "0",
                    "--write", "9876",
                    "--loglevel", "INFO"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            print(write_result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error writing value: {e}")
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")
        
        # Read back the value to verify
        print("\nReading back the value from holding register 0...")
        try:
            read_result = subprocess.run(
                [
                    sys.executable, 
                    "client_cli.py", 
                    "--port", str(port),
                    "--function", "hr",
                    "--address", "0",
                    "--count", "1",
                    "--loglevel", "INFO"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            print(read_result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error reading value: {e}")
        
    finally:
        # Always stop the server
        if 'server_process' in locals():
            stop_server(server_process)
    
    print_header("Test Complete")

if __name__ == "__main__":
    # Clean up potential previous runs
    try:
        # Set a timeout signal in case something gets stuck
        signal.alarm(30)  # 30 seconds timeout
    except AttributeError:
        # alarm not available on Windows
        pass
        
    run_full_test() 