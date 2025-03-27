"""
main.py - Main entry point for the Modbus tools application
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout

from ui import MainWindow as SimulatorWindow
from scanner import ModbusScanner


class MainWindow(QMainWindow):
    """
    Main window that contains both the simulator and scanner
    """
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """
        Initialize the user interface
        """
        self.setWindowTitle("Modbus Tools")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add simulator tab
        self.simulator = SimulatorWindow()
        self.tabs.addTab(self.simulator, "Simulator")
        
        # Add scanner tab
        self.scanner = ModbusScanner()
        self.tabs.addTab(self.scanner, "Scanner")
        
        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)


def setup_logging():
    """
    Set up basic logging configuration
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """
    Main entry point
    """
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
