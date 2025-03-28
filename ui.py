"""
ui.py - Main window and UI components
"""

import logging
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from scanner import ModbusScanner
from simulator import ModbusSimulator

# Set up logger for this module
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main window of the application
    """

    def __init__(self):
        super().__init__()
        logger.debug("Initializing MainWindow")
        self.setWindowTitle("Modbus Simulator")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface
        """
        logger.debug("Setting up UI")

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create simulator tab
        logger.debug("Creating simulator tab")
        simulator_tab = ModbusSimulator()
        tabs.addTab(simulator_tab, "Modbus Simulator")
        
        # Create scanner tab
        logger.debug("Creating scanner tab")
        scanner_tab = ModbusScanner()
        tabs.addTab(scanner_tab, "Modbus Scanner")
        
        logger.debug("UI setup complete")
