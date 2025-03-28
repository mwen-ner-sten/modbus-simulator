"""
simulator.py - Modbus server simulator with register management
"""

import logging
import json
import os
import time
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
    QComboBox,
    QMessageBox,
    QFileDialog,
    QGroupBox,
    QSpinBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer

# Set up logger for this module
logger = logging.getLogger(__name__)

# Register types
REGISTER_TYPES = {
    "Holding Register": "hr",
    "Input Register": "ir",
    "Coil": "co",
    "Discrete Input": "di"
}

# Default values for different register types
DEFAULT_VALUES = {
    "hr": 0,       # Holding register default value
    "ir": 100,     # Input register default value
    "co": True,    # Coil default value
    "di": False    # Discrete input default value
}

# Default register file
DEFAULT_REGISTER_FILE = "registers.json"

class ModbusSimulator(QWidget):
    """
    Widget for simulating a Modbus server with customizable registers
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing ModbusSimulator widget")
        self.server_running = False
        self.registers = self.create_default_registers()
        self.register_file = DEFAULT_REGISTER_FILE
        
        # Auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_registers)
        self.auto_save_timer.start(2000)  # Save every 2 seconds if changes are made
        self.registers_changed = False
        
        self.init_ui()
        
        # Load registers from file if it exists
        self.load_registers_from_default()
        
    def create_default_registers(self):
        """
        Create default register values
        """
        return {
            "hr": {i: DEFAULT_VALUES["hr"] for i in range(10)},        # Holding registers
            "ir": {i: DEFAULT_VALUES["ir"] for i in range(10)},        # Input registers
            "co": {i: DEFAULT_VALUES["co"] for i in range(10)},        # Coils
            "di": {i: DEFAULT_VALUES["di"] for i in range(10)}         # Discrete inputs
        }
        
    def init_ui(self):
        """
        Initialize the user interface
        """
        logger.debug("Setting up ModbusSimulator UI")
        layout = QVBoxLayout()
        
        # Server controls
        server_group = QGroupBox("Server Settings")
        server_layout = QVBoxLayout()
        
        # Connection settings
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("127.0.0.1")
        connection_layout.addWidget(self.host_input)
        
        connection_layout.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(502)
        connection_layout.addWidget(self.port_input)
        
        connection_layout.addWidget(QLabel("Register File:"))
        self.register_file_input = QLineEdit(DEFAULT_REGISTER_FILE)
        connection_layout.addWidget(self.register_file_input)
        
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.toggle_server)
        connection_layout.addWidget(self.start_button)
        
        server_layout.addLayout(connection_layout)
        
        # Auto-restart option
        restart_layout = QHBoxLayout()
        self.auto_restart_checkbox = QCheckBox("Auto-restart server when registers change")
        self.auto_restart_checkbox.setChecked(True)  # Default to enabled
        self.auto_restart_checkbox.setToolTip("Automatically restart the server when register values are modified")
        restart_layout.addWidget(self.auto_restart_checkbox)
        
        # Logging level option
        restart_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        restart_layout.addWidget(self.log_level_combo)
        
        server_layout.addLayout(restart_layout)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Register filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Register Type:"))
        self.register_type = QComboBox()
        self.register_type.addItems(list(REGISTER_TYPES.keys()))
        self.register_type.currentIndexChanged.connect(self.update_register_table)
        filter_layout.addWidget(self.register_type)
        
        # Add register button
        self.add_button = QPushButton("Add Register")
        self.add_button.clicked.connect(self.add_register)
        filter_layout.addWidget(self.add_button)
        
        # Edit register button
        self.edit_button = QPushButton("Edit Register")
        self.edit_button.clicked.connect(self.edit_register)
        filter_layout.addWidget(self.edit_button)
        
        # Remove register button
        self.remove_button = QPushButton("Remove Register")
        self.remove_button.clicked.connect(self.remove_register)
        filter_layout.addWidget(self.remove_button)
        
        # Save button
        self.save_now_button = QPushButton("Save Now")
        self.save_now_button.clicked.connect(self.save_registers_to_default)
        filter_layout.addWidget(self.save_now_button)
        
        layout.addLayout(filter_layout)
        
        # Register table
        self.register_table = QTableWidget()
        self.register_table.setColumnCount(3)
        self.register_table.setHorizontalHeaderLabels(["Address", "Value", "Description"])
        self.register_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.register_table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.register_table)
        
        # File operations
        file_layout = QHBoxLayout()
        
        self.load_button = QPushButton("Load Registers")
        self.load_button.clicked.connect(self.load_registers)
        file_layout.addWidget(self.load_button)
        
        self.save_button = QPushButton("Save Registers")
        self.save_button.clicked.connect(self.save_registers)
        file_layout.addWidget(self.save_button)
        
        # Reset to defaults button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        file_layout.addWidget(self.reset_button)
        
        # Manual restart button
        self.restart_button = QPushButton("Restart Server")
        self.restart_button.clicked.connect(self.restart_server)
        self.restart_button.setEnabled(False)
        file_layout.addWidget(self.restart_button)
        
        layout.addLayout(file_layout)
        
        # Status message
        self.status_label = QLabel("Register changes are auto-saved every 2 seconds")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        logger.debug("ModbusSimulator UI setup complete")
        
        # Initial update
        self.update_register_table()
        
    def update_register_table(self):
        """
        Update the register table based on the selected register type
        """
        register_type = REGISTER_TYPES[self.register_type.currentText()]
        logger.debug(f"Updating register table for type: {register_type}")
        
        # Disconnect cell changed signal to prevent triggering while updating
        self.register_table.cellChanged.disconnect(self.on_cell_changed)
        
        self.register_table.setRowCount(0)
        
        for address, value in self.registers[register_type].items():
            row = self.register_table.rowCount()
            self.register_table.insertRow(row)
            
            # Address item
            address_item = QTableWidgetItem(str(address))
            address_item.setFlags(address_item.flags() & ~Qt.ItemIsEditable)
            self.register_table.setItem(row, 0, address_item)
            
            # Value item
            value_item = QTableWidgetItem(str(value))
            self.register_table.setItem(row, 1, value_item)
            
            # Description item (empty for now)
            self.register_table.setItem(row, 2, QTableWidgetItem(""))
        
        # Reconnect cell changed signal
        self.register_table.cellChanged.connect(self.on_cell_changed)
        
    def on_cell_changed(self, row, column):
        """
        Handle cell value changes in the table
        """
        if column == 1:  # Value column
            try:
                register_type = REGISTER_TYPES[self.register_type.currentText()]
                address = int(self.register_table.item(row, 0).text())
                value_str = self.register_table.item(row, 1).text()
                
                # Convert value based on register type
                if register_type in ["co", "di"]:
                    # Boolean registers (coils and discrete inputs)
                    value = value_str.lower() in ["true", "1", "yes", "y"]
                else:
                    # Numeric registers
                    value = int(value_str)
                
                # Update the register value
                self.registers[register_type][address] = value
                logger.info(f"Cell changed: Updated {register_type}[{address}] to {value}")
                
                # Mark as changed for auto-save
                self.registers_changed = True
                
            except ValueError as e:
                logger.error(f"Invalid value in cell: {str(e)}")
                # Revert the cell to the previous value
                self.update_register_table()
            
    def add_register(self):
        """
        Add a new register
        """
        register_type = REGISTER_TYPES[self.register_type.currentText()]
        logger.debug(f"Adding new register of type: {register_type}")
        
        # Find the next available address
        next_address = 0
        if self.registers[register_type]:
            next_address = max(self.registers[register_type].keys()) + 1
            
        # Add the register with default value
        default_value = DEFAULT_VALUES[register_type]
            
        self.registers[register_type][next_address] = default_value
        self.update_register_table()
        self.registers_changed = True
        self.save_registers_to_default()
        
    def edit_register(self):
        """
        Edit the selected register
        """
        selected_items = self.register_table.selectedItems()
        if not selected_items:
            logger.warning("No register selected for editing")
            QMessageBox.warning(self, "No Selection", "Please select a register to edit")
            return
            
        row = selected_items[0].row()
        address = int(self.register_table.item(row, 0).text())
        register_type = REGISTER_TYPES[self.register_type.currentText()]
        
        logger.debug(f"Editing register type={register_type}, address={address}")
        
        # Get the new value from the table
        try:
            value_str = self.register_table.item(row, 1).text()
            
            # Convert value based on register type
            if register_type in ["co", "di"]:
                # Boolean registers (coils and discrete inputs)
                value = value_str.lower() in ["true", "1", "yes", "y"]
            else:
                # Numeric registers
                value = int(value_str)
                
            self.registers[register_type][address] = value
            logger.info(f"Updated register type={register_type}, address={address}, value={value}")
            
            # Update the table to ensure consistent display
            self.update_register_table()
            self.registers_changed = True
            self.save_registers_to_default()
            
        except ValueError as e:
            logger.error(f"Invalid register value: {str(e)}")
            QMessageBox.warning(self, "Invalid Value", f"Please enter a valid value: {str(e)}")
            
    def remove_register(self):
        """
        Remove the selected register
        """
        selected_items = self.register_table.selectedItems()
        if not selected_items:
            logger.warning("No register selected for removal")
            QMessageBox.warning(self, "No Selection", "Please select a register to remove")
            return
            
        row = selected_items[0].row()
        address = int(self.register_table.item(row, 0).text())
        register_type = REGISTER_TYPES[self.register_type.currentText()]
        
        if address in self.registers[register_type]:
            logger.debug(f"Removing register type={register_type}, address={address}")
            del self.registers[register_type][address]
            self.update_register_table()
            self.registers_changed = True
            self.save_registers_to_default()
    
    def auto_save_registers(self):
        """
        Auto save registers if changed
        """
        if self.registers_changed:
            logger.debug("Auto-saving registers to default file")
            self.save_registers_to_default()
            self.registers_changed = False
        
    def load_registers_from_default(self):
        """
        Load registers from the default file
        """
        if os.path.exists(self.register_file):
            try:
                logger.info(f"Loading registers from default file: {self.register_file}")
                with open(self.register_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert string keys to integers
                for reg_type in ["hr", "ir", "co", "di"]:
                    if reg_type in data:
                        self.registers[reg_type] = {int(k): v for k, v in data[reg_type].items()}
                        logger.info(f"Loaded {len(self.registers[reg_type])} {reg_type} registers")
                        
                logger.info(f"Register contents: {self.registers}")
                self.update_register_table()
                logger.info("Registers loaded from default file")
                
            except Exception as e:
                logger.error(f"Error loading registers from default file: {str(e)}", exc_info=True)
    
    def save_registers_to_default(self):
        """
        Save registers to the default file
        """
        try:
            # Get the current register file from the UI
            self.register_file = self.register_file_input.text()
            
            logger.info(f"Saving registers to default file: {self.register_file}")
            logger.debug(f"Register contents being saved: {self.registers}")
            
            # Convert data for JSON serialization (all keys to strings)
            json_data = {}
            for reg_type, values in self.registers.items():
                json_data[reg_type] = {str(k): v for k, v in values.items()}
                
            with open(self.register_file, 'w') as f:
                json.dump(json_data, f, indent=4)
                
            logger.info("Registers saved to default file")
            self.status_label.setText(f"Registers saved to {self.register_file}")
            
            # Check if we should restart the server
            if self.server_running and self.auto_restart_checkbox.isChecked():
                logger.info("Auto-restart is enabled, restarting server...")
                self.restart_server()
            
        except Exception as e:
            logger.error(f"Error saving registers to default file: {str(e)}", exc_info=True)
            self.status_label.setText(f"Error saving: {str(e)}")
            
    def load_registers(self):
        """
        Load registers from a JSON file
        """
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Registers", "", "JSON Files (*.json)"
        )
        
        if not filename:
            return
            
        try:
            logger.info(f"Loading registers from file: {filename}")
            with open(filename, 'r') as f:
                data = json.load(f)
                
            # Convert string keys to integers
            for reg_type in ["hr", "ir", "co", "di"]:
                if reg_type in data:
                    self.registers[reg_type] = {int(k): v for k, v in data[reg_type].items()}
                    
            self.update_register_table()
            logger.info("Registers loaded successfully")
            QMessageBox.information(self, "Success", "Registers loaded successfully")
            
            # Update the register file input
            self.register_file_input.setText(filename)
            self.register_file = filename
            
            # Save to make sure server gets updated
            self.save_registers_to_default()
            
        except Exception as e:
            logger.error(f"Error loading registers: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load registers: {str(e)}")
        
    def save_registers(self):
        """
        Save registers to a JSON file
        """
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Registers", "", "JSON Files (*.json)"
        )
        
        if not filename:
            return
            
        try:
            logger.info(f"Saving registers to file: {filename}")
            
            # Convert data for JSON serialization (all keys to strings)
            json_data = {}
            for reg_type, values in self.registers.items():
                json_data[reg_type] = {str(k): v for k, v in values.items()}
                
            with open(filename, 'w') as f:
                json.dump(json_data, f, indent=4)
                
            logger.info("Registers saved successfully")
            QMessageBox.information(self, "Success", "Registers saved successfully")
            
            # Update the register file input
            self.register_file_input.setText(filename)
            self.register_file = filename
            
        except Exception as e:
            logger.error(f"Error saving registers: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save registers: {str(e)}")
            
    def reset_to_defaults(self):
        """
        Reset registers to default values
        """
        logger.info("Resetting registers to default values")
        
        self.registers = self.create_default_registers()
        
        self.update_register_table()
        logger.info("Registers reset to defaults")
        
        # Save to make sure server gets updated
        self.save_registers_to_default()
            
    def toggle_server(self):
        """
        Toggle the server state
        """
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def restart_server(self):
        """
        Restart the Modbus server
        """
        logger.info("Restarting Modbus server")
        
        # Stop the server if it's running
        if self.server_running:
            self.stop_server()
            
            # Small delay to ensure the port is released
            time.sleep(2)
        
        # Start the server on the same port
        self.start_server()
            
    def start_server(self):
        """
        Start the Modbus server
        """
        import subprocess
        import sys
        
        logger.info("Starting Modbus server")
        
        # Save registers to make sure server has latest values
        self.save_registers_to_default()
        
        host = self.host_input.text()
        port = self.port_input.value()
        register_file = self.register_file_input.text()
        log_level = self.log_level_combo.currentText()
        
        try:
            # Use a separate process to run the server
            cmd = [
                sys.executable, 
                "server.py", 
                "--host", host, 
                "--port", str(port),
                "--register-file", register_file,
                "--loglevel", log_level
            ]
            self.server_process = subprocess.Popen(cmd)
            
            self.server_running = True
            self.start_button.setText("Stop Server")
            self.restart_button.setEnabled(True)
            logger.info(f"Server started on {host}:{port} with register file {register_file}")
            
            QMessageBox.information(self, "Server Started", f"Modbus server started on {host}:{port}")
            
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")
            
    def stop_server(self):
        """
        Stop the Modbus server
        """
        if hasattr(self, 'server_process'):
            logger.info("Stopping Modbus server")
            
            try:
                self.server_process.terminate()
                self.server_running = False
                self.start_button.setText("Start Server")
                self.restart_button.setEnabled(False)
                logger.info("Server stopped")
                
            except Exception as e:
                logger.error(f"Error stopping server: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to stop server: {str(e)}")
        
    def closeEvent(self, event):
        """
        Handle application shutdown
        """
        if self.server_running:
            self.stop_server() 