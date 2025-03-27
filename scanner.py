"""
scanner.py - Modbus network scanner implementation
"""

import logging
import asyncio
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
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

class ModbusScanner(QWidget):
    """
    Widget for scanning Modbus networks and discovering devices
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """
        Initialize the user interface
        """
        layout = QVBoxLayout()
        
        # Network range input
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("IP Range:"))
        self.ip_start = QLineEdit("192.168.1.1")
        self.ip_end = QLineEdit("192.168.1.254")
        range_layout.addWidget(self.ip_start)
        range_layout.addWidget(QLabel("to"))
        range_layout.addWidget(self.ip_end)
        layout.addLayout(range_layout)
        
        # Port input
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("502")
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)
        
        # Slave ID range
        slave_layout = QHBoxLayout()
        slave_layout.addWidget(QLabel("Slave ID Range:"))
        self.slave_start = QLineEdit("1")
        self.slave_end = QLineEdit("247")
        slave_layout.addWidget(self.slave_start)
        slave_layout.addWidget(QLabel("to"))
        slave_layout.addWidget(self.slave_end)
        layout.addLayout(slave_layout)
        
        # Scan button
        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["IP Address", "Port", "Slave ID", "Status"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.results_table)
        
        self.setLayout(layout)
        
    @pyqtSlot()
    def start_scan(self):
        """
        Start the network scan
        """
        try:
            # Validate inputs
            ip_start = self.ip_start.text()
            ip_end = self.ip_end.text()
            port = int(self.port_input.text())
            slave_start = int(self.slave_start.text())
            slave_end = int(self.slave_end.text())
            
            if not (1 <= slave_start <= 247 and 1 <= slave_end <= 247 and slave_start <= slave_end):
                QMessageBox.warning(self, "Invalid Input", "Slave ID range must be between 1 and 247")
                return
                
            # Clear previous results
            self.results_table.setRowCount(0)
            
            # Disable scan button
            self.scan_button.setEnabled(False)
            
            # Start scanning
            asyncio.create_task(self.scan_network(ip_start, ip_end, port, slave_start, slave_end))
            
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            self.scan_button.setEnabled(True)
            
    async def scan_network(self, ip_start: str, ip_end: str, port: int, slave_start: int, slave_end: int):
        """
        Scan the network for Modbus devices
        
        Args:
            ip_start: Starting IP address
            ip_end: Ending IP address
            port: Port to scan
            slave_start: Starting slave ID
            slave_end: Ending slave ID
        """
        try:
            # Convert IP addresses to integers for range calculation
            start_parts = [int(x) for x in ip_start.split('.')]
            end_parts = [int(x) for x in ip_end.split('.')]
            
            start_ip = sum(part << (24 - 8 * i) for i, part in enumerate(start_parts))
            end_ip = sum(part << (24 - 8 * i) for i, part in enumerate(end_parts))
            
            total_ips = end_ip - start_ip + 1
            total_slaves = slave_end - slave_start + 1
            total_scans = total_ips * total_slaves
            current_scan = 0
            
            for ip_int in range(start_ip, end_ip + 1):
                ip = '.'.join(str((ip_int >> (24 - 8 * i)) & 0xFF) for i in range(4))
                
                for slave_id in range(slave_start, slave_end + 1):
                    try:
                        # Create client
                        client = AsyncModbusTcpClient(ip, port)
                        await client.connect()
                        
                        # Try to read holding registers
                        result = await client.read_holding_registers(0, 1, slave_id=slave_id)
                        
                        if result and not result.isError():
                            # Device found
                            row = self.results_table.rowCount()
                            self.results_table.insertRow(row)
                            self.results_table.setItem(row, 0, QTableWidgetItem(ip))
                            self.results_table.setItem(row, 1, QTableWidgetItem(str(port)))
                            self.results_table.setItem(row, 2, QTableWidgetItem(str(slave_id)))
                            self.results_table.setItem(row, 3, QTableWidgetItem("Found"))
                            
                    except Exception as e:
                        logging.debug(f"Error scanning {ip}:{port} slave {slave_id}: {str(e)}")
                        
                    finally:
                        await client.close()
                        
                    # Update progress
                    current_scan += 1
                    progress = int((current_scan / total_scans) * 100)
                    self.progress_bar.setValue(progress)
                    
        except Exception as e:
            QMessageBox.critical(self, "Scan Error", f"An error occurred during scanning: {str(e)}")
            
        finally:
            self.scan_button.setEnabled(True)
            self.progress_bar.setValue(100) 