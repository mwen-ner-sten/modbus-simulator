"""
scanner.py - Modbus network scanner implementation
"""

import logging
from typing import List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QMessageBox,
    QComboBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ModbusException

# Set up logger for this module
logger = logging.getLogger(__name__)


class ScanThread(QThread):
    """
    Thread for reading Modbus registers
    """
    progress = pyqtSignal(int)
    result_ready = pyqtSignal(str, str, str)
    
    def __init__(self, ip, port, slave_id, function_code, register_address, register_count):
        super().__init__()
        self.ip = ip
        self.port = port
        self.slave_id = slave_id
        self.function_code = function_code
        self.register_address = register_address
        self.register_count = register_count
        logger.debug(f"Initialized ScanThread with IP: {ip}, Port: {port}, Slave ID: {slave_id}")
        
    def run(self):
        """
        Run the read operation
        """
        try:
            logger.info(f"Starting Modbus read operation for {self.ip}:{self.port}")
            logger.debug(f"Parameters: Slave ID={self.slave_id}, Function={self.function_code}, "
                        f"Address={self.register_address}, Count={self.register_count}")
            
            # Create client
            client = ModbusTcpClient(self.ip, self.port)
            logger.debug("Created ModbusTcpClient")
            
            try:
                client.connect()
                logger.debug("Connected to Modbus device")
                
                # Read registers based on function code
                logger.debug(f"Attempting to read registers with function code: {self.function_code}")
                if self.function_code == "Read Holding Registers":
                    result = client.read_holding_registers(self.register_address, self.register_count, unit=self.slave_id)
                elif self.function_code == "Read Input Registers":
                    result = client.read_input_registers(self.register_address, self.register_count, unit=self.slave_id)
                elif self.function_code == "Read Coils":
                    result = client.read_coils(self.register_address, self.register_count, unit=self.slave_id)
                elif self.function_code == "Read Discrete Inputs":
                    result = client.read_discrete_inputs(self.register_address, self.register_count, unit=self.slave_id)
                else:
                    error_msg = f"Unsupported function code: {self.function_code}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                if result and not result.isError():
                    # Format the result
                    if hasattr(result, 'registers'):
                        values = [str(v) for v in result.registers]
                        logger.debug(f"Read {len(values)} register values: {values}")
                    elif hasattr(result, 'bits'):
                        values = [str(v) for v in result.bits]
                        logger.debug(f"Read {len(values)} bit values: {values}")
                    else:
                        values = [str(result)]
                        logger.debug(f"Read single value: {values[0]}")
                    
                    self.result_ready.emit(
                        f"Address {self.register_address}",
                        f"Count: {self.register_count}",
                        f"Values: {', '.join(values)}"
                    )
                    logger.info(f"Successfully read {len(values)} values from address {self.register_address}")
                else:
                    error_msg = "Failed to read registers"
                    logger.error(error_msg)
                    self.result_ready.emit(
                        f"Address {self.register_address}",
                        "Error",
                        error_msg
                    )
                    
            finally:
                client.close()
                logger.debug("Closed Modbus connection")
                
            self.progress.emit(100)
            logger.info("Read operation completed successfully")
                    
        except Exception as e:
            logger.error(f"Error during read operation: {str(e)}", exc_info=True)
            self.result_ready.emit(
                f"Address {self.register_address}",
                "Error",
                str(e)
            )
            self.progress.emit(100)


class ModbusScanner(QWidget):
    """
    Widget for reading Modbus registers
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing ModbusScanner widget")
        self.init_ui()
        
    def init_ui(self):
        """
        Initialize the user interface
        """
        logger.debug("Setting up ModbusScanner UI")
        layout = QVBoxLayout()
        
        # IP and Port input
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("IP Address:"))
        self.ip_input = QLineEdit("127.0.0.1")
        connection_layout.addWidget(self.ip_input)
        
        connection_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("502")
        connection_layout.addWidget(self.port_input)
        
        connection_layout.addWidget(QLabel("Slave ID:"))
        self.slave_id = QLineEdit("1")
        connection_layout.addWidget(self.slave_id)
        
        layout.addLayout(connection_layout)
        
        # Function code selection
        function_layout = QHBoxLayout()
        function_layout.addWidget(QLabel("Function Code:"))
        self.function_code = QComboBox()
        self.function_code.addItems([
            "Read Holding Registers",
            "Read Input Registers",
            "Read Coils",
            "Read Discrete Inputs"
        ])
        function_layout.addWidget(self.function_code)
        layout.addLayout(function_layout)
        
        # Register address and count
        register_layout = QHBoxLayout()
        register_layout.addWidget(QLabel("Register Address:"))
        self.register_address = QLineEdit("0")
        register_layout.addWidget(self.register_address)
        
        register_layout.addWidget(QLabel("Count:"))
        self.register_count = QLineEdit("1")
        register_layout.addWidget(self.register_count)
        
        layout.addLayout(register_layout)
        
        # Read button
        self.read_button = QPushButton("Read Registers")
        self.read_button.clicked.connect(self.start_read)
        layout.addWidget(self.read_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Register", "Count/Status", "Values"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.results_table)
        
        self.setLayout(layout)
        logger.debug("ModbusScanner UI setup complete")
        
    @pyqtSlot()
    def start_read(self):
        """
        Start reading registers
        """
        try:
            logger.info("Starting read operation")
            # Validate inputs
            ip = self.ip_input.text()
            port = int(self.port_input.text())
            slave_id = int(self.slave_id.text())
            register_address = int(self.register_address.text())
            register_count = int(self.register_count.text())
            
            logger.debug(f"Input validation: IP={ip}, Port={port}, Slave ID={slave_id}, "
                        f"Address={register_address}, Count={register_count}")
            
            if not (1 <= slave_id <= 247):
                error_msg = "Slave ID must be between 1 and 247"
                logger.warning(error_msg)
                QMessageBox.warning(self, "Invalid Input", error_msg)
                return
                
            if register_address < 0:
                error_msg = "Register address must be non-negative"
                logger.warning(error_msg)
                QMessageBox.warning(self, "Invalid Input", error_msg)
                return
                
            if register_count < 1:
                error_msg = "Count must be at least 1"
                logger.warning(error_msg)
                QMessageBox.warning(self, "Invalid Input", error_msg)
                return
                
            # Clear previous results
            self.results_table.setRowCount(0)
            logger.debug("Cleared previous results")
            
            # Disable read button
            self.read_button.setEnabled(False)
            logger.debug("Disabled read button")
            
            # Start reading in a separate thread
            self.scan_thread = ScanThread(
                ip, port, slave_id,
                self.function_code.currentText(),
                register_address, register_count
            )
            self.scan_thread.progress.connect(self.update_progress)
            self.scan_thread.result_ready.connect(self.add_result)
            self.scan_thread.finished.connect(self.read_finished)
            self.scan_thread.start()
            logger.info("Started scan thread")
            
        except ValueError as e:
            logger.error(f"Input validation error: {str(e)}")
            QMessageBox.warning(self, "Invalid Input", str(e))
            self.read_button.setEnabled(True)
            
    def update_progress(self, progress):
        """
        Update the progress bar
        """
        logger.debug(f"Updating progress: {progress}%")
        self.progress_bar.setValue(progress)
        
    def add_result(self, register, count, values):
        """
        Add a result to the results table
        """
        logger.debug(f"Adding result: Register={register}, Count={count}, Values={values}")
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(register))
        self.results_table.setItem(row, 1, QTableWidgetItem(count))
        self.results_table.setItem(row, 2, QTableWidgetItem(values))
        
    def read_finished(self):
        """
        Called when the read operation is complete
        """
        logger.info("Read operation finished")
        self.read_button.setEnabled(True)
        self.progress_bar.setValue(100) 