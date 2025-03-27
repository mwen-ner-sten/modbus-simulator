"""
main.py - Main entry point for the Modbus simulator application
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QMetaType

from ui import MainWindow


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
    Main application entry point
    """
    # Set up logging
    setup_logging()

    # Create application
    app = QApplication(sys.argv)

    # Fix QTextCursor threading issue
    # Different versions of PyQt5 have different ways to register types
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
                "Could not register QTextCursor meta type. Threading-related issues might occur."
            )

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
