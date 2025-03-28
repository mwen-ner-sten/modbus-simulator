#!/usr/bin/env python
"""
Main entry point for the Modbus Simulator.

This module launches the GUI application when the package is run directly.
"""

import sys
from PyQt5.QtWidgets import QApplication
from modbus_tools.gui.ui import MainWindow

def main():
    """Run the Modbus Simulator GUI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 