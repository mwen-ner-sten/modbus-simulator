"""
main.py - Main entry point for the Modbus simulator application
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui import MainWindow

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the application
    """
    try:
        logger.debug("Logging setup complete")
        logger.debug("Starting application")
        
        # Create the application
        app = QApplication(sys.argv)
        
        # Create and show the main window
        window = MainWindow()
        window.show()
        
        # Start the event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
