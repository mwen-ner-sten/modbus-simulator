"""
ui.py - User interface components for the Modbus simulator
"""

import sys
import logging
import threading
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QGroupBox,
    QRadioButton,
    QMessageBox,
    QFileDialog,
    QTextEdit,
    QDialog,
)
from PyQt5.QtCore import Qt, QTimer, QMetaType, QObject, pyqtSlot, Q_ARG, QMetaObject
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QTextCursor

from models import ModbusRegister, REGISTER_TYPES, DATA_TYPES, ERROR_BEHAVIORS
from server import ModbusSimulator


class RegisterTableWidget(QTableWidget):
    """
    Custom table widget for displaying Modbus registers
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(12)
        self.setHorizontalHeaderLabels(
            [
                "Address",
                "Name",
                "Value",
                "Data Type",
                "Register Type",
                "Enabled",
                "Error Behavior",
                "Scaling",
                "Offset",
                "Unit",
                "Word Order",
                "Byte Order",
            ]
        )
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )  # Name column stretches
        self.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.Stretch
        )  # Error behavior column stretches
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)

    def populate_table(self, registers):
        """
        Populate the table with registers
        """
        self.setRowCount(0)
        for register in registers:
            self.add_register_row(register)

    def add_register_row(self, register):
        """
        Add a register row to the table
        """
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(str(register.address)))
        self.setItem(row, 1, QTableWidgetItem(register.name))
        self.setItem(row, 2, QTableWidgetItem(str(register.value)))
        self.setItem(row, 3, QTableWidgetItem(register.data_type))
        self.setItem(row, 4, QTableWidgetItem(register.register_type))
        self.setItem(row, 5, QTableWidgetItem("Yes" if register.enabled else "No"))
        self.setItem(row, 6, QTableWidgetItem(register.error_behavior))
        self.setItem(row, 7, QTableWidgetItem(str(register.scaling_factor)))
        self.setItem(row, 8, QTableWidgetItem(str(register.offset)))
        self.setItem(row, 9, QTableWidgetItem(register.unit))
        self.setItem(row, 10, QTableWidgetItem(register.word_order))
        self.setItem(row, 11, QTableWidgetItem(register.byte_order))

    def update_register_row(self, row, register):
        """
        Update a register row in the table
        """
        self.setItem(row, 0, QTableWidgetItem(str(register.address)))
        self.setItem(row, 1, QTableWidgetItem(register.name))
        self.setItem(row, 2, QTableWidgetItem(str(register.value)))
        self.setItem(row, 3, QTableWidgetItem(register.data_type))
        self.setItem(row, 4, QTableWidgetItem(register.register_type))
        self.setItem(row, 5, QTableWidgetItem("Yes" if register.enabled else "No"))
        self.setItem(row, 6, QTableWidgetItem(register.error_behavior))
        self.setItem(row, 7, QTableWidgetItem(str(register.scaling_factor)))
        self.setItem(row, 8, QTableWidgetItem(str(register.offset)))
        self.setItem(row, 9, QTableWidgetItem(register.unit))
        self.setItem(row, 10, QTableWidgetItem(register.word_order))
        self.setItem(row, 11, QTableWidgetItem(register.byte_order))


class RegisterEditDialog(QDialog):
    """
    Dialog for editing a Modbus register
    """

    def __init__(self, register=None, parent=None):
        super().__init__(parent)
        self.register = register if register else ModbusRegister(0)
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface
        """
        self.setWindowTitle("Edit Register")
        self.layout = QVBoxLayout()

        # Create form layout
        form_layout = QVBoxLayout()

        # Address and Name
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Address:"))
        self.address_input = QSpinBox()
        self.address_input.setRange(0, 65535)
        self.address_input.setValue(self.register.address)
        h_layout.addWidget(self.address_input)

        h_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit(self.register.name)
        h_layout.addWidget(self.name_input)
        form_layout.addLayout(h_layout)

        # Register type and Data type
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Register Type:"))
        self.reg_type_combo = QComboBox()
        self.reg_type_combo.addItems(list(REGISTER_TYPES.keys()))
        self.reg_type_combo.setCurrentText(self.register.register_type)
        h_layout.addWidget(self.reg_type_combo)

        h_layout.addWidget(QLabel("Data Type:"))
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(list(DATA_TYPES.keys()))
        self.data_type_combo.setCurrentText(self.register.data_type)
        h_layout.addWidget(self.data_type_combo)
        form_layout.addLayout(h_layout)

        # Value
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit(str(self.register.value))
        h_layout.addWidget(self.value_input)
        form_layout.addLayout(h_layout)

        # Scaling and Offset
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Scaling Factor:"))
        self.scaling_input = QLineEdit(str(self.register.scaling_factor))
        self.scaling_input.setValidator(QDoubleValidator())
        h_layout.addWidget(self.scaling_input)

        h_layout.addWidget(QLabel("Offset:"))
        self.offset_input = QLineEdit(str(self.register.offset))
        self.offset_input.setValidator(QDoubleValidator())
        h_layout.addWidget(self.offset_input)

        h_layout.addWidget(QLabel("Unit:"))
        self.unit_input = QLineEdit(self.register.unit)
        h_layout.addWidget(self.unit_input)
        form_layout.addLayout(h_layout)

        # Byte and Word order
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Word Order:"))
        self.word_order_combo = QComboBox()
        self.word_order_combo.addItems(["BIG", "LITTLE"])
        self.word_order_combo.setCurrentText(self.register.word_order)
        h_layout.addWidget(self.word_order_combo)

        h_layout.addWidget(QLabel("Byte Order:"))
        self.byte_order_combo = QComboBox()
        self.byte_order_combo.addItems(["BIG", "LITTLE"])
        self.byte_order_combo.setCurrentText(self.register.byte_order)
        h_layout.addWidget(self.byte_order_combo)
        form_layout.addLayout(h_layout)

        # Enabled checkbox
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(self.register.enabled)
        form_layout.addWidget(self.enabled_check)

        # Error behavior
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Error Behavior:"))
        self.error_combo = QComboBox()
        self.error_combo.addItems(list(ERROR_BEHAVIORS.keys()))
        self.error_combo.setCurrentText(self.register.error_behavior)
        h_layout.addWidget(self.error_combo)
        form_layout.addLayout(h_layout)

        # Description
        form_layout.addWidget(QLabel("Description:"))
        self.description_input = QLineEdit(self.register.description)
        form_layout.addWidget(self.description_input)

        self.layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_register)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def save_register(self):
        """
        Save the register data from the form
        """
        try:
            self.register.address = self.address_input.value()
            self.register.name = self.name_input.text()
            self.register.register_type = self.reg_type_combo.currentText()
            self.register.data_type = self.data_type_combo.currentText()

            # Parse value based on data type
            data_type = self.data_type_combo.currentText()
            value_str = self.value_input.text()

            if "FLOAT" in data_type:
                self.register.value = float(value_str)
            elif "INT" in data_type or "UINT" in data_type:
                self.register.value = int(value_str)
            elif data_type == "BOOLEAN":
                self.register.value = bool(int(value_str))
            else:
                self.register.value = value_str

            self.register.scaling_factor = float(self.scaling_input.text())
            self.register.offset = float(self.offset_input.text())
            self.register.unit = self.unit_input.text()
            self.register.word_order = self.word_order_combo.currentText()
            self.register.byte_order = self.byte_order_combo.currentText()
            self.register.enabled = self.enabled_check.isChecked()
            self.register.error_behavior = self.error_combo.currentText()
            self.register.description = self.description_input.text()

            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")

    def accept(self):
        """
        Accept the dialog
        """
        self.done(QDialog.Accepted)

    def get_register(self):
        """
        Get the edited register

        Returns:
            ModbusRegister: The edited register
        """
        return self.register


class LogTextHandler(logging.Handler):
    """
    Custom logging handler that redirects log messages to a QTextEdit
    in a thread-safe way
    """

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

    def emit(self, record):
        msg = self.format(record)
        # Use invokeMethod to update the UI from a non-GUI thread
        QMetaObject.invokeMethod(
            self.text_edit, "append", Qt.QueuedConnection, Q_ARG(str, msg)
        )


class MainWindow(QMainWindow):
    """
    Main window for the Modbus simulator
    """

    def __init__(self):
        super().__init__()
        self.simulator = ModbusSimulator()

        # Register QTextCursor meta type to fix threading issues
        # Try multiple approaches to handle different PyQt versions
        try:
            # For newer versions of PyQt5
            QMetaType.registerType("QTextCursor")
        except AttributeError:
            try:
                # For older versions of PyQt5
                from PyQt5.QtCore import qRegisterMetaType

                qRegisterMetaType("QTextCursor")
            except (ImportError, AttributeError):
                logging.warning(
                    "Could not register QTextCursor meta type in UI. Threading-related issues might occur."
                )

        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface
        """
        self.setWindowTitle("PyModbus Simulator")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()

        # Create registers tab
        registers_tab = QWidget()
        registers_layout = QVBoxLayout()

        # Create register table
        self.register_table = RegisterTableWidget()
        registers_layout.addWidget(self.register_table)

        # Create register control buttons
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Register")
        self.add_btn.clicked.connect(self.add_register)
        button_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edit Register")
        self.edit_btn.clicked.connect(self.edit_register)
        button_layout.addWidget(self.edit_btn)

        self.duplicate_btn = QPushButton("Duplicate Register")
        self.duplicate_btn.clicked.connect(self.duplicate_register)
        button_layout.addWidget(self.duplicate_btn)

        self.remove_btn = QPushButton("Remove Register")
        self.remove_btn.clicked.connect(self.remove_register)
        button_layout.addWidget(self.remove_btn)

        registers_layout.addLayout(button_layout)

        # Add bulk controls
        bulk_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import from CSV")
        self.import_btn.clicked.connect(self.import_registers)
        bulk_layout.addWidget(self.import_btn)

        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.export_registers)
        bulk_layout.addWidget(self.export_btn)

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_configuration)
        bulk_layout.addWidget(self.save_btn)

        self.load_btn = QPushButton("Load Configuration")
        self.load_btn.clicked.connect(self.load_configuration)
        bulk_layout.addWidget(self.load_btn)

        registers_layout.addLayout(bulk_layout)

        registers_tab.setLayout(registers_layout)

        # Create server tab
        server_tab = QWidget()
        server_layout = QVBoxLayout()

        # Create server settings group
        server_group = QGroupBox("Server Settings")
        server_settings_layout = QVBoxLayout()

        # Create connection settings
        connection_layout = QHBoxLayout()
        self.tcp_radio = QRadioButton("TCP")
        self.tcp_radio.setChecked(True)
        connection_layout.addWidget(self.tcp_radio)

        self.rtu_radio = QRadioButton("RTU")
        connection_layout.addWidget(self.rtu_radio)

        server_settings_layout.addLayout(connection_layout)

        # TCP settings
        self.tcp_settings = QWidget()
        tcp_layout = QHBoxLayout()
        tcp_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("localhost")
        tcp_layout.addWidget(self.host_input)

        tcp_layout.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(502)
        tcp_layout.addWidget(self.port_input)

        self.tcp_settings.setLayout(tcp_layout)
        server_settings_layout.addWidget(self.tcp_settings)

        # RTU settings
        self.rtu_settings = QWidget()
        rtu_layout = QHBoxLayout()
        rtu_layout.addWidget(QLabel("Port:"))
        self.serial_port_input = QLineEdit("COM1")
        rtu_layout.addWidget(self.serial_port_input)

        rtu_layout.addWidget(QLabel("Baudrate:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        rtu_layout.addWidget(self.baudrate_combo)

        rtu_layout.addWidget(QLabel("Parity:"))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["N", "E", "O"])
        rtu_layout.addWidget(self.parity_combo)

        rtu_layout.addWidget(QLabel("Data Bits:"))
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["7", "8"])
        self.databits_combo.setCurrentText("8")
        rtu_layout.addWidget(self.databits_combo)

        rtu_layout.addWidget(QLabel("Stop Bits:"))
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        rtu_layout.addWidget(self.stopbits_combo)

        self.rtu_settings.setLayout(rtu_layout)
        self.rtu_settings.setVisible(False)
        server_settings_layout.addWidget(self.rtu_settings)

        # Set up radio button connections
        self.tcp_radio.toggled.connect(self.toggle_connection_settings)
        self.rtu_radio.toggled.connect(self.toggle_connection_settings)

        # Slave ID
        slave_layout = QHBoxLayout()
        slave_layout.addWidget(QLabel("Slave ID:"))
        self.slave_id_input = QSpinBox()
        self.slave_id_input.setRange(1, 255)
        self.slave_id_input.setValue(1)
        slave_layout.addWidget(self.slave_id_input)
        server_settings_layout.addLayout(slave_layout)

        # Timeouts
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Response Timeout (ms):"))
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(0, 10000)
        self.timeout_input.setValue(1000)
        timeout_layout.addWidget(self.timeout_input)
        server_settings_layout.addLayout(timeout_layout)

        server_group.setLayout(server_settings_layout)
        server_layout.addWidget(server_group)

        # Create server control buttons
        server_control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Server")
        self.start_btn.clicked.connect(self.start_server)
        server_control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        server_control_layout.addWidget(self.stop_btn)

        server_layout.addLayout(server_control_layout)

        # Create server status
        self.status_label = QLabel("Server Status: Stopped")
        server_layout.addWidget(self.status_label)

        server_tab.setLayout(server_layout)

        # Create log tab
        log_tab = QWidget()
        log_layout = QVBoxLayout()

        # Create log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        log_tab.setLayout(log_layout)

        # Add tabs to tab widget
        self.tabs.addTab(registers_tab, "Registers")
        self.tabs.addTab(server_tab, "Server")
        self.tabs.addTab(log_tab, "Log")

        main_layout.addWidget(self.tabs)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Set up timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)  # Update every second

        # Initialize with registers
        self.update_register_table()

        # Set up logging
        self.setup_logging()

    def setup_logging(self):
        """
        Set up logging to the log text area
        """
        # Create handler for the log text edit
        log_handler = LogTextHandler(self.log_text)
        log_handler.setLevel(logging.INFO)

        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addHandler(log_handler)

    def toggle_connection_settings(self):
        """
        Toggle between TCP and RTU connection settings
        """
        self.tcp_settings.setVisible(self.tcp_radio.isChecked())
        self.rtu_settings.setVisible(self.rtu_radio.isChecked())

    def update_ui(self):
        """
        Update the user interface periodically
        """
        server_running = self.simulator.is_server_running()
        self.start_btn.setEnabled(not server_running)
        self.stop_btn.setEnabled(server_running)

        if server_running:
            self.status_label.setText("Server Status: Running")
        else:
            self.status_label.setText("Server Status: Stopped")

    def update_register_table(self):
        """
        Update the register table
        """
        registers = self.simulator.datastore.get_all_registers()
        self.register_table.populate_table(registers)

    def add_register(self):
        """
        Add a new register
        """
        dialog = RegisterEditDialog(ModbusRegister(0), self)
        if dialog.exec_() == QDialog.Accepted:
            register = dialog.get_register()
            self.simulator.datastore.add_register(register)
            self.update_register_table()

    def edit_register(self):
        """
        Edit the selected register
        """
        selected_rows = self.register_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, "No Selection", "Please select a register to edit."
            )
            return

        row = selected_rows[0].row()
        address = int(self.register_table.item(row, 0).text())
        register = self.simulator.datastore.get_register(address)

        if register:
            dialog = RegisterEditDialog(register, self)
            if dialog.exec_() == QDialog.Accepted:
                self.update_register_table()

    def duplicate_register(self):
        """
        Duplicate the selected register
        """
        selected_rows = self.register_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, "No Selection", "Please select a register to duplicate."
            )
            return

        row = selected_rows[0].row()
        address = int(self.register_table.item(row, 0).text())
        original_register = self.simulator.datastore.get_register(address)

        if original_register:
            # Create a new register with the same properties but a different address
            new_register = ModbusRegister(
                address=original_register.address + 1,
                name=original_register.name + " (Copy)",
                value=original_register.value,
                data_type=original_register.data_type,
                register_type=original_register.register_type,
                enabled=original_register.enabled,
                error_behavior=original_register.error_behavior,
                description=original_register.description,
            )
            new_register.scaling_factor = original_register.scaling_factor
            new_register.offset = original_register.offset
            new_register.unit = original_register.unit
            new_register.word_order = original_register.word_order
            new_register.byte_order = original_register.byte_order

            self.simulator.datastore.add_register(new_register)
            self.update_register_table()

    def remove_register(self):
        """
        Remove the selected register
        """
        selected_rows = self.register_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, "No Selection", "Please select a register to remove."
            )
            return

        row = selected_rows[0].row()
        address = int(self.register_table.item(row, 0).text())

        confirmation = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete register at address {address}?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirmation == QMessageBox.Yes:
            self.simulator.datastore.remove_register(address)
            self.update_register_table()

    def import_registers(self):
        """
        Import registers from a CSV file
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Import Registers", "", "CSV Files (*.csv)"
        )
        if file_name:
            try:
                self.simulator.datastore.import_from_csv(file_name)
                self.update_register_table()
                QMessageBox.information(
                    self, "Import Success", "Registers imported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error", f"Failed to import registers: {str(e)}"
                )

    def export_registers(self):
        """
        Export registers to a CSV file
        """
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Registers", "", "CSV Files (*.csv)"
        )
        if file_name:
            try:
                self.simulator.datastore.export_to_csv(file_name)
                QMessageBox.information(
                    self, "Export Success", "Registers exported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export registers: {str(e)}"
                )

    def save_configuration(self):
        """
        Save the configuration to a JSON file
        """
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "JSON Files (*.json)"
        )
        if file_name:
            try:
                self.simulator.datastore.save_to_file(file_name)
                QMessageBox.information(
                    self, "Save Success", "Configuration saved successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Save Error", f"Failed to save configuration: {str(e)}"
                )

    def load_configuration(self):
        """
        Load the configuration from a JSON file
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON Files (*.json)"
        )
        if file_name:
            try:
                self.simulator.datastore.load_from_file(file_name)
                self.update_register_table()
                QMessageBox.information(
                    self, "Load Success", "Configuration loaded successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Load Error", f"Failed to load configuration: {str(e)}"
                )

    def start_server(self):
        """
        Start the Modbus server
        """
        if self.simulator.is_server_running():
            QMessageBox.warning(self, "Server Running", "Server is already running.")
            return

        try:
            # Update slave ID from UI
            self.simulator.datastore.slave_id = self.slave_id_input.value()

            # Start server based on connection type
            if self.tcp_radio.isChecked():
                host = self.host_input.text()
                port = self.port_input.value()
                success = self.simulator.start_server(host=host, port=port, mode="TCP")
            else:
                # RTU mode implementation
                QMessageBox.information(
                    self, "Not Implemented", "RTU mode is not fully implemented yet."
                )
                return

            if success:
                self.status_label.setText("Server Status: Running")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                logging.info(f"Server started on {host}:{port}")
            else:
                QMessageBox.critical(self, "Server Error", "Failed to start server.")

        except Exception as e:
            QMessageBox.critical(
                self, "Server Error", f"Failed to start server: {str(e)}"
            )

    def stop_server(self):
        """
        Stop the Modbus server
        """
        if not self.simulator.is_server_running():
            QMessageBox.warning(self, "Server Not Running", "Server is not running.")
            return

        try:
            success = self.simulator.stop_server()
            if success:
                self.status_label.setText("Server Status: Stopped")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                logging.info("Server stopped")
            else:
                QMessageBox.critical(self, "Server Error", "Failed to stop server.")
        except Exception as e:
            QMessageBox.critical(
                self, "Server Error", f"Failed to stop server: {str(e)}"
            )

    def closeEvent(self, event):
        """
        Handle the close event
        """
        if self.simulator.is_server_running():
            reply = QMessageBox.question(
                self,
                "Server Running",
                "The server is still running. Do you want to stop it and quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.simulator.stop_server()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
