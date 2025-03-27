"""
server.py - Modbus server implementation for the simulator
"""

import logging
import asyncio
import threading
from typing import Tuple, Optional, Any
from pymodbus.server.asynchronous import StartTcpServer, StartSerialServer
from pymodbus.device import ModbusDeviceIdentification

from models import ModbusDataStore


class ModbusSimulator:
    """
    Modbus simulator class that handles the server functionality
    """

    def __init__(self):
        self.server = None
        self.running = False
        self.datastore = ModbusDataStore()
        self.server_thread = None
        self.loop = None
        self._identity = None

    def start_server(
        self, host: str = "localhost", port: int = 502, mode: str = "TCP"
    ) -> bool:
        """
        Start the Modbus server

        Args:
            host: Host address (for TCP)
            port: Port number (for TCP)
            mode: Connection mode ("TCP" or "RTU")

        Returns:
            bool: True if server started successfully, False otherwise
        """
        if self.running:
            return False

        # Create the server context
        context = self.datastore.create_context()

        # Create the identity information
        self._identity = ModbusDeviceIdentification()
        self._identity.VendorName = "PyModbus Simulator"
        self._identity.ProductCode = "PM"
        self._identity.VendorUrl = "https://github.com/pymodbus-dev/pymodbus"
        self._identity.ProductName = "PyModbus Simulator"
        self._identity.ModelName = "PyModbus Simulator"
        self._identity.MajorMinorRevision = "1.0"

        # Start the server based on the mode
        if mode == "TCP":
            logging.info(f"Starting Modbus TCP Server on {host}:{port}")
            self.loop = asyncio.new_event_loop()
            self.server_thread = threading.Thread(
                target=self._run_server, args=(host, port, context)
            )
            self.server_thread.daemon = True
            self.server_thread.start()
            self.running = True
            return True
        else:
            # RTU mode not fully implemented yet
            logging.warning("RTU mode not fully implemented")
            return False

    def _run_server(self, host: str, port: int, context: Any) -> None:
        """
        Run the server in a separate thread

        Args:
            host: Host address
            port: Port number
            context: Modbus server context
        """
        asyncio.set_event_loop(self.loop)

        # Use empty dictionaries for the custom_functions and identity parameters
        # Add framer=None to use the default TCP framer
        self.loop.run_until_complete(
            StartTcpServer(context, identity=self._identity, address=(host, port))
        )
        self.loop.run_forever()

    def stop_server(self) -> bool:
        """
        Stop the Modbus server

        Returns:
            bool: True if server stopped successfully, False otherwise
        """
        if not self.running:
            return False

        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.server_thread.join(timeout=1.0)
            self.loop = None
            self.server_thread = None
            self.running = False
            logging.info("Modbus server stopped")
            return True
        return False

    def is_server_running(self) -> bool:
        """
        Check if the server is running

        Returns:
            bool: True if server is running, False otherwise
        """
        return self.running
