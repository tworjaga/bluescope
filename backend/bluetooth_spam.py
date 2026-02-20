"""
Bluetooth Spam Module - Packet injection and spamming capabilities for BlueScope
For security testing and research purposes only
"""

import asyncio
import random
import struct
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime

logger = logging.getLogger(__name__)


class SpamMode(Enum):
    """Spam operation modes"""
    ADVERTISING = auto()  # Spam advertising packets
    CONNECTION = auto()   # Spam connection requests
    L2CAP = auto()        # Spam L2CAP packets
    ATT = auto()          # Spam ATT/GATT requests
    RANDOM = auto()       # Random packet spam


@dataclass
class SpamConfig:
    """Spam configuration"""
    mode: SpamMode = SpamMode.ADVERTISING
    target_address: Optional[str] = None
    packet_rate: int = 10  # packets per second
    duration: int = 60  # seconds, 0 = infinite
    payload_size: int = 31  # max advertising payload
    randomize_data: bool = True
    channel: int = 37  # BLE advertising channel


class BluetoothSpammer:
    """
    Bluetooth packet spammer for security testing
    WARNING: Use only for authorized testing and research
    """
    
    def __init__(self, config: Optional[SpamConfig] = None):
        self.config = config or SpamConfig()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            'packets_sent': 0,
            'start_time': None,
            'errors': 0
        }
        
        # Callbacks
        self.on_packet_sent: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        logger.info("BluetoothSpammer initialized")
    
    async def start(self) -> bool:
        """Start spamming"""
        if self.is_running:
            logger.warning("Spammer already running")
            return False
        
        self.is_running = True
        self._stop_event.clear()
        self.stats['start_time'] = datetime.now()
        self.stats['packets_sent'] = 0
        self.stats['errors'] = 0
        
        # Start spamming task
        self._task = asyncio.create_task(self._spam_loop())
        
        logger.info(f"Started spamming in {self.config.mode.name} mode")
        return True
    
    async def stop(self):
        """Stop spamming"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Stopped spamming. Sent {self.stats['packets_sent']} packets")
    
    async def _spam_loop(self):
        """Main spamming loop"""
        interval = 1.0 / self.config.packet_rate
        
        try:
            while self.is_running and not self._stop_event.is_set():
                try:
                    # Generate and send packet based on mode
                    packet = self._generate_packet()
                    await self._send_packet(packet)
                    
                    self.stats['packets_sent'] += 1
                    
                    if self.on_packet_sent:
                        self.on_packet_sent(self.stats['packets_sent'])
                    
                    # Check duration
                    if self.config.duration > 0:
                        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                        if elapsed >= self.config.duration:
                            logger.info("Duration limit reached")
                            break
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    self.stats['errors'] += 1
                    logger.error(f"Spam error: {e}")
                    if self.on_error:
                        self.on_error(e)
                    
        except asyncio.CancelledError:
            logger.debug("Spam loop cancelled")
    
    def _generate_packet(self) -> bytes:
        """Generate spam packet based on mode"""
        if self.config.mode == SpamMode.ADVERTISING:
            return self._generate_advertising_packet()
        elif self.config.mode == SpamMode.CONNECTION:
            return self._generate_connection_packet()
        elif self.config.mode == SpamMode.L2CAP:
            return self._generate_l2cap_packet()
        elif self.config.mode == SpamMode.ATT:
            return self._generate_att_packet()
        elif self.config.mode == SpamMode.RANDOM:
            return self._generate_random_packet()
        else:
            return self._generate_advertising_packet()
    
    def _generate_advertising_packet(self) -> bytes:
        """Generate advertising packet"""
        # Advertising header
        header = bytes([
            0x00,  # ADV_IND
            random.randint(6, 37),  # Random length
        ])
        
        # Advertising data
        if self.config.randomize_data:
            # Random manufacturer data
            company_id = random.randint(0x0000, 0xFFFF)
            payload = bytes([
                0x02, 0x01, 0x06,  # Flags
                0x03, 0x03, 0xAA, 0xFE,  # Service UUID
                0x06, 0x16,  # Manufacturer data header
                (company_id >> 0) & 0xFF,  # Company ID LSB
                (company_id >> 8) & 0xFF,  # Company ID MSB
            ])
            # Add random data
            remaining = self.config.payload_size - len(payload)
            if remaining > 0:
                payload += bytes(random.randint(0, 255) for _ in range(remaining))
        else:
            # Fixed pattern
            payload = b"\x02\x01\x06\x03\x03\xAA\xFE" + b"\x00" * (self.config.payload_size - 7)
        
        return header + payload[:self.config.payload_size]
    
    def _generate_connection_packet(self) -> bytes:
        """Generate connection request packet"""
        # LL_CONNECTION_REQ
        header = bytes([0x05, 0x22])  # CONNECT_IND, 34 bytes
        
        # Initiator address (random)
        init_addr = bytes(random.randint(0, 255) for _ in range(6))
        
        # Advertiser address (target or random)
        if self.config.target_address:
            adv_addr = bytes.fromhex(self.config.target_address.replace(':', ''))
        else:
            adv_addr = bytes(random.randint(0, 255) for _ in range(6))
        
        # Access address
        access_addr = struct.pack('<I', random.randint(0, 0xFFFFFFFF))
        
        # CRC init
        crc_init = bytes(random.randint(0, 255) for _ in range(3))
        
        # WinSize, WinOffset, Interval, Latency, Timeout
        conn_params = struct.pack('<BHHHH', 
            random.randint(1, 20),  # WinSize (1 byte)
            random.randint(0, 100),   # WinOffset (2 bytes)
            random.randint(6, 3200),  # Interval (2 bytes)
            random.randint(0, 499),   # Latency (2 bytes)
            random.randint(10, 3200)  # Timeout (2 bytes)
        )

        
        # Channel map
        channel_map = bytes(random.randint(0, 255) for _ in range(5))
        
        # Hop and SCA
        hop_sca = bytes([random.randint(5, 16) | (random.randint(0, 7) << 5)])
        
        return header + init_addr + adv_addr + access_addr + crc_init + conn_params + channel_map + hop_sca
    
    def _generate_l2cap_packet(self) -> bytes:
        """Generate L2CAP packet"""
        # L2CAP header
        length = random.randint(2, 100)
        cid = random.choice([0x0004, 0x0005, 0x0006])  # ATT, LE signaling, SMP
        
        header = struct.pack('<HH', length, cid)
        
        # Payload
        payload = bytes(random.randint(0, 255) for _ in range(length))
        
        return header + payload
    
    def _generate_att_packet(self) -> bytes:
        """Generate ATT/GATT packet"""
        # ATT opcode
        opcode = random.choice([
            0x01,  # Error response
            0x04,  # Find Information Request
            0x06,  # Find By Type Value Request
            0x08,  # Read By Type Request
            0x0A,  # Read Request
            0x0C,  # Read Blob Request
            0x10,  # Read By Group Type Request
            0x12,  # Write Request
        ])
        
        # Handle or parameters
        if opcode in [0x04, 0x06, 0x08, 0x10]:
            # Range request
            start_handle = struct.pack('<H', random.randint(0x0001, 0xFFFF))
            end_handle = struct.pack('<H', random.randint(0x0001, 0xFFFF))
            return bytes([opcode]) + start_handle + end_handle
        elif opcode in [0x0A, 0x0C, 0x12]:
            # Single handle
            handle = struct.pack('<H', random.randint(0x0001, 0xFFFF))
            return bytes([opcode]) + handle
        else:
            return bytes([opcode, random.randint(0, 255)])
    
    def _generate_random_packet(self) -> bytes:
        """Generate completely random packet"""
        length = random.randint(2, 255)
        return bytes(random.randint(0, 255) for _ in range(length))
    
    async def _send_packet(self, packet: bytes):
        """Send packet (placeholder - would use actual Bluetooth interface)"""
        # In a real implementation, this would use the Bluetooth adapter
        # For now, just log the packet
        logger.debug(f"Sending {len(packet)} byte packet")
        
        # Simulate sending delay
        await asyncio.sleep(0.001)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get spam statistics"""
        elapsed = 0
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'packets_sent': self.stats['packets_sent'],
            'packet_rate': self.stats['packets_sent'] / max(elapsed, 0.001),
            'errors': self.stats['errors'],
            'elapsed_seconds': elapsed,
            'is_running': self.is_running,
            'mode': self.config.mode.name
        }


class BLEAdvertisementSpammer(BluetoothSpammer):
    """Specialized spammer for BLE advertisements"""
    
    def __init__(self):
        super().__init__(SpamConfig(
            mode=SpamMode.ADVERTISING,
            packet_rate=100,  # High rate for advertising
            randomize_data=True
        ))
        
        # Common company IDs for spoofing
        self.company_ids = [
            0x004C,  # Apple
            0x0006,  # Microsoft
            0x0075,  # Samsung
            0x00E0,  # Google
            0x0583,  # Fitbit
            0x0157,  # Anker
        ]
    
    def _generate_advertising_packet(self) -> bytes:
        """Generate realistic advertising packet"""
        company_id = random.choice(self.company_ids)
        
        # Build iBeacon-like or Eddystone-like packet
        packet_type = random.choice(['ibeacon', 'eddystone', 'random'])
        
        if packet_type == 'ibeacon':
            # iBeacon format
            payload = bytes([
                0x02, 0x01, 0x06,  # Flags
                0x1A, 0xFF,        # Manufacturer data length and type
                (company_id >> 0) & 0xFF,  # Company ID LSB
                (company_id >> 8) & 0xFF,  # Company ID MSB
                0x02, 0x15,        # iBeacon indicator
            ])
            # UUID (16 bytes)
            payload += bytes(random.randint(0, 255) for _ in range(16))
            # Major, Minor (2 bytes each)
            payload += struct.pack('>HH', random.randint(0, 65535), random.randint(0, 65535))
            # TX Power
            payload += bytes([random.randint(-100, 0) & 0xFF])
            
        elif packet_type == 'eddystone':
            # Eddystone-UID format
            payload = bytes([
                0x02, 0x01, 0x06,  # Flags
                0x03, 0x03, 0xAA, 0xFE,  # Eddystone service UUID
                0x17, 0x16, 0xAA, 0xFE,  # Service data length and type
                0x00,  # Eddystone-UID frame type
                random.randint(-100, 0) & 0xFF,  # TX Power
            ])
            # Namespace (10 bytes) + Instance (6 bytes)
            payload += bytes(random.randint(0, 255) for _ in range(16))
            # Reserved
            payload += bytes([0x00, 0x00])
            
        else:
            # Random manufacturer data
            payload = bytes([
                0x02, 0x01, 0x06,  # Flags
                0x06, 0xFF,        # Manufacturer data
                (company_id >> 0) & 0xFF,
                (company_id >> 8) & 0xFF,
            ])
            payload += bytes(random.randint(0, 255) for _ in range(27))
        
        return payload[:31]  # Max advertising payload


def test_bluetooth_spam():
    """Test Bluetooth spammer"""
    print("\n" + "="*60)
    print("Bluetooth Spam Module Test")
    print("="*60)
    
    # Test 1: Basic spammer
    print("\n1. Testing basic spammer:")
    spammer = BluetoothSpammer(SpamConfig(
        mode=SpamMode.ADVERTISING,
        packet_rate=5,
        duration=2
    ))
    
    async def test_basic():
        await spammer.start()
        await asyncio.sleep(2.5)
        stats = spammer.get_statistics()
        print(f"  Sent {stats['packets_sent']} packets")
        print(f"  Rate: {stats['packet_rate']:.1f} pps")
    
    asyncio.run(test_basic())
    
    # Test 2: Advertisement spammer
    print("\n2. Testing advertisement spammer:")
    adv_spammer = BLEAdvertisementSpammer()
    adv_spammer.config.duration = 1
    
    async def test_adv():
        await adv_spammer.start()
        await asyncio.sleep(1.5)
        stats = adv_spammer.get_statistics()
        print(f"  Sent {stats['packets_sent']} advertising packets")
    
    asyncio.run(test_adv())
    
    # Test 3: Packet generation
    print("\n3. Testing packet generation:")
    spammer = BluetoothSpammer()
    
    packets = {
        'Advertising': spammer._generate_advertising_packet(),
        'Connection': spammer._generate_connection_packet(),
        'L2CAP': spammer._generate_l2cap_packet(),
        'ATT': spammer._generate_att_packet(),
        'Random': spammer._generate_random_packet(),
    }
    
    for name, packet in packets.items():
        print(f"  {name}: {len(packet)} bytes - {packet[:20].hex()}...")
    
    print("\n All spam module tests completed")
    print("WARNING: Use only for authorized security testing!")
    return True


if __name__ == "__main__":
    test_bluetooth_spam()
