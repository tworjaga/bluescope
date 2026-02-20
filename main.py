#!/usr/bin/env python3
"""
BlueScope - Main Entry Point
Enterprise Bluetooth monitoring and analysis platform
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from frontend.ui.main_window import MainWindow
from analytics.behavior_engine.main import BehaviorEngine
from analytics.anomaly_engine.main import AnomalyEngine
import logging


def setup_logging():
    """Configure logging system"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "bluescope.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BlueScope - Enterprise Bluetooth Monitoring Platform"
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no GUI)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/settings.yaml',
        help='Configuration file path'
    )
    
    return parser.parse_args()


def run_gui(args, logger):
    """Run application with GUI"""
    logger.info("Starting BlueScope with GUI")
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("BlueScope")
    app.setOrganizationName("BlueScope")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow(config_path=args.config)
    window.show()
    
    # Run application
    sys.exit(app.exec())


async def run_headless(args, logger):
    """Run application in headless mode"""
    logger.info("Starting BlueScope in headless mode")
    
    # Initialize engines
    behavior_engine = BehaviorEngine()
    anomaly_engine = AnomalyEngine()
    
    # Start engines
    await behavior_engine.start()
    await anomaly_engine.start()
    
    logger.info("Engines started, running...")
    
    try:
        # Run until interrupted
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    finally:
        # Stop engines
        await behavior_engine.stop()
        await anomaly_engine.stop()
        logger.info("Engines stopped")


def main():
    """Main entry point"""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup logging
        logger = setup_logging()
        
        logger.info("=" * 60)
        logger.info("BlueScope - Enterprise Bluetooth Monitoring Platform")
        logger.info("=" * 60)
        
        # Run in appropriate mode
        if args.headless:
            asyncio.run(run_headless(args, logger))
        else:
            run_gui(args, logger)
            
    except ImportError as e:
        print(f"\n[ERROR] Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("  pip install -r requirements-minimal.txt")
        print("\nOr for full features:")
        print("  pip install -r requirements.txt")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        print(f"\nCheck logs/bluescope.log for details")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
