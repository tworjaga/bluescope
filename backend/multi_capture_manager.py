"""
Multi-Device Capture Manager - Handles multiple Bluetooth adapters simultaneously
Supports concurrent capture from multiple BLE dongles, sniffers, and SDRs
"""

import sys
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import queue
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.capture_manager import CaptureManager, BLEDevice, BLEPacket, get_capture_manager


logger = logging.getLogger(__name__)


@dataclass
class CaptureDevice:
    """Represents a capture device configuration"""
    device_id: str
    device_type: str  # 'bleak', 'rust', 'mock'
    name: str
    is_active: bool = False
    capture_manager: Optional[CaptureManager] = None
    stats: Dict[str, Any] = field(default_factory=dict)


class MultiCaptureManager:
    """
    Manages multiple Bluetooth capture devices simultaneously
    Aggregates data from all devices into unified view
    """
    
    def __init__(self):
        self.devices: Dict[str, CaptureDevice] = {}
        self.is_capturing = False
        self._lock = threading.RLock()
        
        # Unified data storage
        self.all_devices: Dict[str, BLEDevice] = {}
        self.all_packets: deque = deque(maxlen=100000)
        
        # Global callbacks
        self.on_device_discovered: Optional[Callable[[BLEDevice, str], None]] = None
        self.on_packet_received: Optional[Callable[[BLEPacket, str], None]] = None
        
        # Global statistics
        self.global_stats = {
            'total_packets': 0,
            'total_devices': 0,
            'active_captures': 0,
            'start_time': None
        }
        
        logger.info("MultiCaptureManager initialized")
    
    def detect_devices(self) -> List[Dict[str, Any]]:
        """
        Detect available Bluetooth capture devices on the system
        Returns list of device information dictionaries
        """
        detected = []
        
        # Detect BLE adapters via Bleak
        try:
            import bleak
            from bleak import BleakScanner
            
            async def scan_adapters():
                try:
                    scanner = BleakScanner()
                    # Just check if we can access the adapter
                    await scanner.start()
                    await asyncio.sleep(0.5)
                    await scanner.stop()
                    return True
                except Exception as e:
                    logger.debug(f"Bleak adapter check: {e}")
                    return False
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bleak_available = loop.run_until_complete(scan_adapters())
            loop.close()
            
            if bleak_available:
                detected.append({
                    'device_id': 'bleak_default',
                    'device_type': 'bleak',
                    'name': 'Default BLE Adapter',
                    'description': 'System default Bluetooth adapter'
                })
                
        except ImportError:
            logger.debug("Bleak not available for device detection")
        except Exception as e:
            logger.debug(f"Error detecting Bleak adapters: {e}")
        
        # Detect serial ports (potential nRF Sniffers)
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Check for likely Bluetooth sniffers
                is_likely_sniffer = any([
                    'nrf' in port.description.lower(),
                    'sniffer' in port.description.lower(),
                    'ble' in port.description.lower(),
                    'nordic' in port.description.lower(),
                    port.vid == 0x1915  # Nordic Semiconductor VID
                ])
                
                if is_likely_sniffer or 'ttyACM' in port.device or 'COM' in port.device:
                    detected.append({
                        'device_id': port.device,
                        'device_type': 'rust',  # Use Rust agent for nRF
                        'name': f"nRF Sniffer ({port.description[:30]})",
                        'description': f"Serial port: {port.device}"
                    })
                    
        except ImportError:
            logger.debug("pyserial not available for port detection")
        except Exception as e:
            logger.debug(f"Error detecting serial ports: {e}")
        
        # Add mock device for testing
        detected.append({
            'device_id': 'mock_0',
            'device_type': 'mock',
            'name': 'Mock Device (Testing)',
            'description': 'Simulated capture for testing'
        })
        
        logger.info(f"Detected {len(detected)} capture devices")
        return detected
    
    def add_device(self, device_id: str, device_type: str, name: str) -> bool:
        """
        Add a capture device to the manager
        
        Args:
            device_id: Unique identifier for the device
            device_type: 'bleak', 'rust', or 'mock'
            name: Human-readable name
        
        Returns:
            True if device was added successfully
        """
        with self._lock:
            if device_id in self.devices:
                logger.warning(f"Device {device_id} already exists")
                return False
            
            # Create capture manager for this device
            config = {
                'backend': device_type,
                'device_id': device_id
            }
            
            capture_mgr = CaptureManager(config)
            
            # Set up callbacks that include device_id
            capture_mgr.on_device_discovered = lambda d: self._on_device(d, device_id)
            capture_mgr.on_packet_received = lambda p: self._on_packet(p, device_id)
            
            device = CaptureDevice(
                device_id=device_id,
                device_type=device_type,
                name=name,
                is_active=False,
                capture_manager=capture_mgr,
                stats={}
            )
            
            self.devices[device_id] = device
            logger.info(f"Added capture device: {name} ({device_id})")
            return True
    
    def remove_device(self, device_id: str) -> bool:
        """Remove a capture device"""
        with self._lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            
            # Stop if active
            if device.is_active:
                asyncio.create_task(self._stop_device(device_id))
            
            del self.devices[device_id]
            logger.info(f"Removed capture device: {device_id}")
            return True
    
    async def start_all(self):
        """Start capture on all devices"""
        logger.info("Starting capture on all devices...")
        self.is_capturing = True
        self.global_stats['start_time'] = datetime.now()
        
        tasks = []
        for device_id in self.devices:
            tasks.append(self._start_device(device_id))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Started {self.global_stats['active_captures']} capture devices")
    
    async def stop_all(self):
        """Stop capture on all devices"""
        logger.info("Stopping all captures...")
        self.is_capturing = False
        
        tasks = []
        for device_id in list(self.devices.keys()):
            tasks.append(self._stop_device(device_id))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All captures stopped")
    
    async def start_device(self, device_id: str) -> bool:
        """Start capture on a specific device"""
        return await self._start_device(device_id)
    
    async def _start_device(self, device_id: str) -> bool:
        """Internal method to start a device"""
        with self._lock:
            if device_id not in self.devices:
                logger.error(f"Device not found: {device_id}")
                return False
            
            device = self.devices[device_id]
            
            if device.is_active:
                logger.warning(f"Device already active: {device_id}")
                return True
            
            try:
                # Start the capture manager
                await device.capture_manager.start_capture()
                device.is_active = True
                self.global_stats['active_captures'] += 1
                
                logger.info(f"Started capture on {device.name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start {device_id}: {e}")
                return False
    
    async def stop_device(self, device_id: str) -> bool:
        """Stop capture on a specific device"""
        return await self._stop_device(device_id)
    
    async def _stop_device(self, device_id: str) -> bool:
        """Internal method to stop a device"""
        with self._lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            
            if not device.is_active:
                return True
            
            try:
                await device.capture_manager.stop_capture()
                device.is_active = False
                self.global_stats['active_captures'] -= 1
                
                logger.info(f"Stopped capture on {device.name}")
                return True
                
            except Exception as e:
                logger.error(f"Error stopping {device_id}: {e}")
                return False
    
    def _on_device(self, device: BLEDevice, source_id: str):
        """Handle device discovery from a capture source"""
        # Merge with global device list
        if device.address not in self.all_devices:
            self.all_devices[device.address] = device
            self.global_stats['total_devices'] = len(self.all_devices)
            
            # Call global callback
            if self.on_device_discovered:
                self.on_device_discovered(device, source_id)
        else:
            # Update existing device
            existing = self.all_devices[device.address]
            existing.rssi = device.rssi
            existing.last_seen = device.last_seen
            existing.packet_count += device.packet_count
    
    def _on_packet(self, packet: BLEPacket, source_id: str):
        """Handle packet from a capture source"""
        # Add to global packet list
        self.all_packets.append(packet)
        self.global_stats['total_packets'] += 1
        
        # Call global callback
        if self.on_packet_received:
            self.on_packet_received(packet, source_id)
    
    def get_all_devices(self) -> List[BLEDevice]:
        """Get all discovered devices from all sources"""
        with self._lock:
            return list(self.all_devices.values())
    
    def get_all_packets(self, limit: int = 1000) -> List[BLEPacket]:
        """Get recent packets from all sources"""
        with self._lock:
            return list(self.all_packets)[-limit:]
    
    def get_device_stats(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific device"""
        with self._lock:
            if device_id not in self.devices:
                return None
            
            device = self.devices[device_id]
            if device.capture_manager:
                return device.capture_manager.get_statistics()
            return None
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics from all devices"""
        with self._lock:
            stats = self.global_stats.copy()
            
            # Calculate uptime
            if stats['start_time']:
                stats['uptime'] = (datetime.now() - stats['start_time']).total_seconds()
            else:
                stats['uptime'] = 0
            
            # Add per-device stats
            stats['devices'] = {}
            for device_id, device in self.devices.items():
                if device.capture_manager:
                    stats['devices'][device_id] = {
                        'name': device.name,
                        'type': device.device_type,
                        'is_active': device.is_active,
                        'stats': device.capture_manager.get_statistics()
                    }
            
            return stats
    
    def get_active_devices(self) -> List[CaptureDevice]:
        """Get list of currently active capture devices"""
        with self._lock:
            return [d for d in self.devices.values() if d.is_active]
    
    def clear_all_data(self):
        """Clear all captured data"""
        with self._lock:
            self.all_devices.clear()
            self.all_packets.clear()
            self.global_stats['total_packets'] = 0
            self.global_stats['total_devices'] = 0
            
            for device in self.devices.values():
                if device.capture_manager:
                    device.capture_manager.clear_devices()
                    device.capture_manager.clear_packets()
            
            logger.info("All capture data cleared")


# Global multi-capture manager instance
_multi_capture_manager: Optional[MultiCaptureManager] = None


def get_multi_capture_manager() -> MultiCaptureManager:
    """Get or create global multi-capture manager instance"""
    global _multi_capture_manager
    if _multi_capture_manager is None:
        _multi_capture_manager = MultiCaptureManager()
    return _multi_capture_manager


async def test_multi_capture():
    """Test multi-device capture functionality"""
    print("\n" + "="*60)
    print("Multi-Device Capture Test")
    print("="*60)
    
    manager = get_multi_capture_manager()
    
    # Detect available devices
    print("\nDetecting capture devices...")
    detected = manager.detect_devices()
    print(f"Found {len(detected)} devices:")
    for dev in detected:
        print(f"  - {dev['name']} ({dev['device_type']})")
    
    # Add mock devices for testing
    print("\nAdding test devices...")
    manager.add_device('mock_1', 'mock', 'Mock Device 1')
    manager.add_device('mock_2', 'mock', 'Mock Device 2')
    
    # Set up callbacks
    def on_device(device, source):
        print(f"   [{source}] Device: {device.name}")
    
    def on_packet(packet, source):
        pass  # Too noisy to print every packet
    
    manager.on_device_discovered = on_device
    manager.on_packet_received = on_packet
    
    # Start all captures
    print("\nStarting all captures for 5 seconds...")
    await manager.start_all()
    
    # Let it run
    await asyncio.sleep(5)
    
    # Stop all
    print("\nStopping all captures...")
    await manager.stop_all()
    
    # Print stats
    stats = manager.get_global_stats()
    print(f"\nGlobal Statistics:")
    print(f"  Total packets: {stats['total_packets']}")
    print(f"  Total devices: {stats['total_devices']}")
    print(f"  Active captures: {stats['active_captures']}")
    print(f"  Uptime: {stats['uptime']:.1f}s")
    
    return stats['total_packets'] > 0


if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_multi_capture())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")
