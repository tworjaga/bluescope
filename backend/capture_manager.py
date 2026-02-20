"""
Capture Manager - Handles real Bluetooth capture via multiple backends
Supports: Bleak (cross-platform), PyBluez, and external Rust agent
"""

import asyncio
import logging
import subprocess
import json
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import queue

logger = logging.getLogger(__name__)


@dataclass
class BLEDevice:
    """Bluetooth Low Energy device information"""
    address: str
    name: str = ""
    rssi: int = 0
    manufacturer_data: Dict[int, bytes] = field(default_factory=dict)
    service_uuids: List[str] = field(default_factory=list)
    tx_power: Optional[int] = None
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    packet_count: int = 0
    is_connected: bool = False


@dataclass
class BLEPacket:
    """Bluetooth Low Energy packet"""
    timestamp: datetime
    device_address: str
    packet_type: str  # ADV_IND, ADV_DIRECT_IND, ADV_NONCONN_IND, SCAN_REQ, SCAN_RSP, CONNECT_REQ
    channel: int
    rssi: int
    data: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)


class CaptureManager:
    """
    Manages Bluetooth capture from multiple sources
    Supports real hardware capture and simulation mode
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_capturing = False
        self.capture_thread = None
        self.packet_queue = queue.Queue(maxsize=10000)
        self.devices: Dict[str, BLEDevice] = {}
        self.packets: deque = deque(maxlen=100000)
        
        # Callbacks
        self.on_device_discovered: Optional[Callable[[BLEDevice], None]] = None
        self.on_packet_received: Optional[Callable[[BLEPacket], None]] = None
        self.on_anomaly_detected: Optional[Callable[[Dict], None]] = None
        
        # Statistics
        self.stats = {
            'total_packets': 0,
            'total_devices': 0,
            'packets_per_second': 0.0,
            'start_time': None
        }
        
        # Capture backend
        self.backend = None
        self.backend_type = self.config.get('backend', 'bleak')  # bleak, pybluez, rust, mock
        
        logger.info(f"CaptureManager initialized with backend: {self.backend_type}")
    
    async def start_capture(self):
        """Start Bluetooth capture (non-blocking)"""
        if self.is_capturing:
            logger.warning("Capture already running")
            return
        
        logger.info("Starting Bluetooth capture...")
        self.is_capturing = True
        self.stats['start_time'] = datetime.now()
        
        try:
            # Start capture in background task so this method returns immediately
            if self.backend_type == 'bleak':
                asyncio.create_task(self._start_bleak_capture())
            elif self.backend_type == 'rust':
                asyncio.create_task(self._start_rust_capture())
            elif self.backend_type == 'mock':
                asyncio.create_task(self._start_mock_capture())
            else:
                logger.error(f"Unknown backend: {self.backend_type}")
                self.is_capturing = False
        except Exception as e:
            logger.error(f"Failed to start capture: {e}")
            self.is_capturing = False
            raise

    
    async def stop_capture(self):
        """Stop Bluetooth capture"""
        if not self.is_capturing:
            return
        
        logger.info("Stopping Bluetooth capture...")
        self.is_capturing = False
        
        if self.backend:
            try:
                await self.backend.stop()
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
        
        logger.info("Capture stopped")
    
    async def _start_bleak_capture(self):
        """Start capture using Bleak library"""
        try:
            from bleak import BleakScanner
            from bleak.backends.device import BLEDevice as BleakDevice
            
            def detection_callback(device: BleakDevice, advertisement_data):
                if not self.is_capturing:
                    return
                
                # Update or create device
                ble_device = self._update_device_from_advertisement(device, advertisement_data)
                
                # Create packet from advertisement
                packet = BLEPacket(
                    timestamp=datetime.now(),
                    device_address=device.address,
                    packet_type='ADV_IND',
                    channel=37,  # Advertising channel
                    rssi=advertisement_data.rssi,
                    data=advertisement_data.manufacturer_data.get(0x004C, b''),  # Apple manufacturer data
                    metadata={
                        'local_name': advertisement_data.local_name,
                        'service_uuids': advertisement_data.service_uuids,
                        'manufacturer_data': dict(advertisement_data.manufacturer_data),
                        'tx_power': advertisement_data.tx_power
                    }
                )
                
                self._process_packet(packet)
            
            self.backend = BleakScanner(detection_callback)
            await self.backend.start()
            logger.info("Bleak scanner started")
            
            # Keep running until stopped
            while self.is_capturing:
                await asyncio.sleep(0.1)
            
            await self.backend.stop()
            
        except ImportError:
            logger.error("Bleak not installed. Install with: pip install bleak")
            raise
        except Exception as e:
            logger.error(f"Error in Bleak capture: {e}")
            raise
    
    async def _start_rust_capture(self):
        """Start capture using Rust agent via subprocess"""
        try:
            rust_agent_path = self.config.get('rust_agent_path', 'agents/bt-capture/target/release/bt-capture')
            
            logger.info(f"Starting Rust agent: {rust_agent_path}")
            
            process = subprocess.Popen(
                [rust_agent_path, '--config', 'config.toml'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.backend = process
            
            # Read output in separate thread
            def read_output():
                while self.is_capturing and process.poll() is None:
                    try:
                        line = process.stdout.readline()
                        if line:
                            self._process_rust_output(line.strip())
                    except Exception as e:
                        logger.error(f"Error reading Rust agent output: {e}")
            
            threading.Thread(target=read_output, daemon=True).start()
            
            # Monitor process
            while self.is_capturing and process.poll() is None:
                await asyncio.sleep(0.5)
            
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
                
        except Exception as e:
            logger.error(f"Error starting Rust agent: {e}")
            raise
    
    async def _start_mock_capture(self):
        """Start mock capture for testing"""
        logger.info("Starting mock capture")
        
        import random
        
        mock_devices = [
            ('AA:BB:CC:DD:EE:01', 'iPhone 12', -65),
            ('AA:BB:CC:DD:EE:02', 'Samsung Galaxy', -72),
            ('AA:BB:CC:DD:EE:03', 'Fitbit Charge', -80),
            ('AA:BB:CC:DD:EE:04', 'AirPods Pro', -55),
            ('AA:BB:CC:DD:EE:05', 'Unknown Device', -68),
        ]
        
        while self.is_capturing:
            # Simulate device discovery
            if random.random() < 0.3:  # 30% chance per iteration
                addr, name, base_rssi = random.choice(mock_devices)
                
                # Vary RSSI slightly
                rssi = base_rssi + random.randint(-5, 5)
                
                # Create packet
                packet = BLEPacket(
                    timestamp=datetime.now(),
                    device_address=addr,
                    packet_type=random.choice(['ADV_IND', 'SCAN_RSP', 'ADV_NONCONN_IND']),
                    channel=random.choice([37, 38, 39]),
                    rssi=rssi,
                    data=bytes([random.randint(0, 255) for _ in range(random.randint(10, 50))]),
                    metadata={
                        'local_name': name,
                        'manufacturer_data': {0x004C: b'\\x02\\x15' + bytes([random.randint(0, 255) for _ in range(20)])},
                        'tx_power': random.randint(-12, 4)
                    }
                )
                
                self._process_packet(packet)
            
            # Random delay between packets
            await asyncio.sleep(random.uniform(0.05, 0.5))
    
    def _process_rust_output(self, line: str):
        """Process output from Rust agent"""
        try:
            data = json.loads(line)
            
            packet = BLEPacket(
                timestamp=datetime.now(),
                device_address=data.get('address', 'unknown'),
                packet_type=data.get('type', 'ADV_IND'),
                channel=data.get('channel', 37),
                rssi=data.get('rssi', -70),
                data=bytes.fromhex(data.get('data', '')),
                metadata=data.get('metadata', {})
            )
            
            self._process_packet(packet)
            
        except json.JSONDecodeError:
            logger.debug(f"Rust agent: {line}")
        except Exception as e:
            logger.error(f"Error processing Rust output: {e}")
    
    def _update_device_from_advertisement(self, device, advertisement_data) -> BLEDevice:
        """Update device info from advertisement data"""
        address = device.address
        
        if address not in self.devices:
            ble_device = BLEDevice(
                address=address,
                name=advertisement_data.local_name or device.name or "Unknown",
                rssi=advertisement_data.rssi,
                manufacturer_data=dict(advertisement_data.manufacturer_data),
                service_uuids=list(advertisement_data.service_uuids),
                tx_power=advertisement_data.tx_power,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                packet_count=1
            )

            self.devices[address] = ble_device
            
            if self.on_device_discovered:
                self.on_device_discovered(ble_device)
        else:
            ble_device = self.devices[address]
            ble_device.rssi = advertisement_data.rssi
            ble_device.last_seen = datetime.now()
            ble_device.packet_count += 1
            
            # Update manufacturer data
            ble_device.manufacturer_data.update(advertisement_data.manufacturer_data)
            
            # Update service UUIDs
            for uuid in advertisement_data.service_uuids:
                if uuid not in ble_device.service_uuids:
                    ble_device.service_uuids.append(uuid)
        
        return ble_device
    
    def _process_packet(self, packet: BLEPacket):
        """Process captured packet"""
        # Store packet
        self.packets.append(packet)
        
        # Create or update device
        if packet.device_address not in self.devices:
            # Create new device from packet metadata
            metadata = packet.metadata or {}
            device_name = metadata.get('local_name', 'Unknown')
            
            self.devices[packet.device_address] = BLEDevice(
                address=packet.device_address,
                name=device_name,
                rssi=packet.rssi,
                first_seen=packet.timestamp,
                last_seen=packet.timestamp,
                packet_count=1

            )
            
            # Call device discovered callback
            if self.on_device_discovered:
                self.on_device_discovered(self.devices[packet.device_address])
        else:
            # Update existing device
            device = self.devices[packet.device_address]
            device.last_seen = packet.timestamp
            device.packet_count += 1
            device.rssi = packet.rssi  # Update with latest RSSI
        
        # Update statistics
        self.stats['total_packets'] += 1
        self._update_packet_rate()
        
        # Call callback
        if self.on_packet_received:
            self.on_packet_received(packet)

    
    def _update_packet_rate(self):
        """Update packets per second calculation"""
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            if elapsed > 0:
                self.stats['packets_per_second'] = self.stats['total_packets'] / elapsed
    
    def get_devices(self) -> List[BLEDevice]:
        """Get list of discovered devices"""
        return list(self.devices.values())
    
    def get_packets(self, limit: int = 1000) -> List[BLEPacket]:
        """Get recent packets"""
        return list(self.packets)[-limit:]
    
    def get_device_by_address(self, address: str) -> Optional[BLEDevice]:
        """Get device by MAC address"""
        return self.devices.get(address)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get capture statistics"""
        return {
            **self.stats,
            'total_devices': len(self.devices),
            'is_capturing': self.is_capturing,
            'backend': self.backend_type,
            'uptime': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        }
    
    def clear_devices(self):
        """Clear device list"""
        self.devices.clear()
        logger.info("Device list cleared")
    
    def clear_packets(self):
        """Clear packet history"""
        self.packets.clear()
        self.stats['total_packets'] = 0
        logger.info("Packet history cleared")


# Global capture manager instance
_capture_manager: Optional[CaptureManager] = None


def get_capture_manager(config: Optional[Dict[str, Any]] = None) -> CaptureManager:
    """Get or create global capture manager instance"""
    global _capture_manager
    if _capture_manager is None:
        _capture_manager = CaptureManager(config)
    return _capture_manager
