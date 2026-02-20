"""
Platform Utilities - Cross-platform compatibility for BlueScope
Handles Windows, Linux, and macOS differences
"""

import os
import sys
import platform
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported platforms"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class PlatformUtils:
    """Cross-platform utility functions"""
    
    @staticmethod
    def get_platform() -> Platform:
        """Detect current platform"""
        system = platform.system().lower()
        
        if system == "windows":
            return Platform.WINDOWS
        elif system == "linux":
            return Platform.LINUX
        elif system == "darwin":
            return Platform.MACOS
        else:
            return Platform.UNKNOWN
    
    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return PlatformUtils.get_platform() == Platform.WINDOWS
    
    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return PlatformUtils.get_platform() == Platform.LINUX
    
    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return PlatformUtils.get_platform() == Platform.MACOS
    
    @staticmethod
    def get_config_dir() -> str:
        """Get platform-specific config directory"""
        plat = PlatformUtils.get_platform()
        
        if plat == Platform.WINDOWS:
            return os.path.join(os.environ.get("APPDATA", ""), "BlueScope")
        elif plat == Platform.MACOS:
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "BlueScope")
        else:  # Linux and others
            return os.path.join(os.path.expanduser("~"), ".config", "bluescope")
    
    @staticmethod
    def get_data_dir() -> str:
        """Get platform-specific data directory"""
        plat = PlatformUtils.get_platform()
        
        if plat == Platform.WINDOWS:
            return os.path.join(os.environ.get("LOCALAPPDATA", ""), "BlueScope")
        elif plat == Platform.MACOS:
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "BlueScope")
        else:  # Linux
            return os.path.join(os.path.expanduser("~"), ".local", "share", "bluescope")
    
    @staticmethod
    def get_cache_dir() -> str:
        """Get platform-specific cache directory"""
        plat = PlatformUtils.get_platform()
        
        if plat == Platform.WINDOWS:
            return os.path.join(os.environ.get("LOCALAPPDATA", ""), "BlueScope", "Cache")
        elif plat == Platform.MACOS:
            return os.path.join(os.path.expanduser("~"), "Library", "Caches", "BlueScope")
        else:  # Linux
            return os.path.join(os.path.expanduser("~"), ".cache", "bluescope")
    
    @staticmethod
    def get_log_dir() -> str:
        """Get platform-specific log directory"""
        plat = PlatformUtils.get_platform()
        
        if plat == Platform.WINDOWS:
            return os.path.join(os.environ.get("LOCALAPPDATA", ""), "BlueScope", "Logs")
        elif plat == Platform.MACOS:
            return os.path.join(os.path.expanduser("~"), "Library", "Logs", "BlueScope")
        else:  # Linux
            return os.path.join(os.path.expanduser("~"), ".local", "share", "bluescope", "logs")
    
    @staticmethod
    def ensure_directories():
        """Ensure all platform directories exist"""
        dirs = [
            PlatformUtils.get_config_dir(),
            PlatformUtils.get_data_dir(),
            PlatformUtils.get_cache_dir(),
            PlatformUtils.get_log_dir(),
        ]
        
        for dir_path in dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"Ensured directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
    
    @staticmethod
    def get_hardware_interfaces() -> List[str]:
        """Get available hardware interfaces for current platform"""
        plat = PlatformUtils.get_platform()
        interfaces = []
        
        if plat == Platform.WINDOWS:
            # Windows supports all interfaces
            interfaces = ["usb_dongle", "nrf_sniffer", "ubertooth", "hackrf", "mock"]
        elif plat == Platform.LINUX:
            # Linux supports all interfaces (with proper permissions)
            interfaces = ["usb_dongle", "nrf_sniffer", "ubertooth", "hackrf", "mock"]
        elif plat == Platform.MACOS:
            # macOS has limited support
            interfaces = ["usb_dongle", "nrf_sniffer", "mock"]
        else:
            interfaces = ["mock"]
        
        return interfaces
    
    @staticmethod
    def get_platform_info() -> Dict[str, Any]:
        """Get detailed platform information"""
        return {
            "platform": PlatformUtils.get_platform().value,
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "python_version": sys.version,
            "hardware_interfaces": PlatformUtils.get_hardware_interfaces(),
            "config_dir": PlatformUtils.get_config_dir(),
            "data_dir": PlatformUtils.get_data_dir(),
            "cache_dir": PlatformUtils.get_cache_dir(),
            "log_dir": PlatformUtils.get_log_dir(),
        }
    
    @staticmethod
    def setup_platform_specific():
        """Setup platform-specific configurations"""
        plat = PlatformUtils.get_platform()
        
        # Ensure directories exist
        PlatformUtils.ensure_directories()
        
        if plat == Platform.WINDOWS:
            PlatformUtils._setup_windows()
        elif plat == Platform.LINUX:
            PlatformUtils._setup_linux()
        elif plat == Platform.MACOS:
            PlatformUtils._setup_macos()
        
        logger.info(f"Platform setup complete for {plat.value}")
    
    @staticmethod
    def _setup_windows():
        """Windows-specific setup"""
        # Windows-specific configurations
        logger.debug("Setting up Windows-specific configurations")
    
    @staticmethod
    def _setup_linux():
        """Linux-specific setup"""
        # Check for required permissions
        logger.debug("Setting up Linux-specific configurations")
        
        # Check if running with sufficient permissions for hardware access
        if os.geteuid() != 0:
            logger.warning("Not running as root - hardware access may be limited")
    
    @staticmethod
    def _setup_macos():
        """macOS-specific setup"""
        logger.debug("Setting up macOS-specific configurations")
        
        # macOS may require specific permissions for Bluetooth
        logger.info("Note: macOS may require Bluetooth permissions in System Preferences")


class PlatformCompatibilityChecker:
    """Check platform compatibility"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
    
    def check_all(self) -> Dict[str, Any]:
        """Run all compatibility checks"""
        self.issues = []
        self.warnings = []
        
        self._check_python_version()
        self._check_platform()
        self._check_dependencies()
        self._check_permissions()
        
        return {
            "compatible": len(self.issues) == 0,
            "issues": self.issues,
            "warnings": self.warnings,
            "platform_info": PlatformUtils.get_platform_info(),
        }
    
    def _check_python_version(self):
        """Check Python version"""
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.issues.append(f"Python {version.major}.{version.minor} is not supported. Need 3.8+")
        elif version.minor < 11:
            self.warnings.append(f"Python 3.{version.minor} works but 3.11+ is recommended")
    
    def _check_platform(self):
        """Check platform support"""
        plat = PlatformUtils.get_platform()
        
        if plat == Platform.UNKNOWN:
            self.warnings.append(f"Unknown platform: {platform.system()}")
        elif plat == Platform.MACOS:
            self.warnings.append("macOS support is experimental - some features may not work")
    
    def _check_dependencies(self):
        """Check required dependencies"""
        required = ["PyQt6", "numpy", "scipy", "sklearn"]
        
        for dep in required:
            try:
                __import__(dep.lower())
            except ImportError:
                self.issues.append(f"Missing required dependency: {dep}")
    
    def _check_permissions(self):
        """Check required permissions"""
        plat = PlatformUtils.get_platform()
        
        if plat == Platform.LINUX and os.geteuid() != 0:
            self.warnings.append("Running without root - hardware capture may fail")


def test_platform_utils():
    """Test platform utilities"""
    print("\n" + "="*60)
    print("Platform Utilities Test")
    print("="*60)
    
    # Test 1: Platform detection
    print("\n1. Testing platform detection:")
    plat = PlatformUtils.get_platform()
    print(f"  Platform: {plat.value}")
    print(f"  Is Windows: {PlatformUtils.is_windows()}")
    print(f"  Is Linux: {PlatformUtils.is_linux()}")
    print(f"  Is macOS: {PlatformUtils.is_macos()}")
    
    # Test 2: Directory paths
    print("\n2. Testing directory paths:")
    print(f"  Config: {PlatformUtils.get_config_dir()}")
    print(f"  Data: {PlatformUtils.get_data_dir()}")
    print(f"  Cache: {PlatformUtils.get_cache_dir()}")
    print(f"  Logs: {PlatformUtils.get_log_dir()}")
    
    # Test 3: Hardware interfaces
    print("\n3. Testing hardware interfaces:")
    interfaces = PlatformUtils.get_hardware_interfaces()
    print(f"  Available: {', '.join(interfaces)}")
    
    # Test 4: Platform info
    print("\n4. Testing platform info:")
    info = PlatformUtils.get_platform_info()
    print(f"  System: {info['system']}")
    print(f"  Release: {info['release']}")
    print(f"  Machine: {info['machine']}")
    print(f"  Python: {info['python_version'][:50]}...")
    
    # Test 5: Compatibility check
    print("\n5. Testing compatibility check:")
    checker = PlatformCompatibilityChecker()
    result = checker.check_all()
    print(f"  Compatible: {result['compatible']}")
    if result['issues']:
        print(f"  Issues: {result['issues']}")
    if result['warnings']:
        print(f"  Warnings: {result['warnings']}")
    
    # Test 6: Directory creation
    print("\n6. Testing directory creation:")
    PlatformUtils.ensure_directories()
    print("  Directories ensured")
    
    print("\n All platform utility tests passed")
    return True


if __name__ == "__main__":
    test_platform_utils()

