"""
Advanced Protocol Decoders - Extended protocol support for BlueScope
Implements decoders for Zigbee, Thread, 802.15.4, and proprietary protocols
"""

import struct
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Supported advanced protocols"""
    ZIGBEE = "zigbee"
    THREAD = "thread"
    IEEE_802_15_4 = "ieee_802_15_4"
    ANT_PLUS = "ant_plus"
    Z_WAVE = "z_wave"
    PROPRIETARY = "proprietary"


@dataclass
class AdvancedProtocolFrame:
    """Generic advanced protocol frame"""
    protocol: ProtocolType
    timestamp: float
    channel: int
    rssi: int
    source_addr: str
    dest_addr: str
    frame_type: str
    payload: bytes
    metadata: Dict[str, Any]


class ZigbeeDecoder:
    """Zigbee protocol decoder"""
    
    # Zigbee frame types
    FRAME_TYPES = {
        0x01: "Data",
        0x02: "Ack",
        0x03: "Command",
        0x04: "Beacon",
    }
    
    def decode(self, data: bytes, channel: int = 11, rssi: int = -80) -> Optional[AdvancedProtocolFrame]:
        """Decode Zigbee frame"""
        if len(data) < 9:
            return None
        
        try:
            # Parse MAC header
            frame_control = data[0]
            seq_num = data[1]
            dest_pan_id = struct.unpack('<H', data[2:4])[0]
            dest_addr = struct.unpack('<H', data[4:6])[0]
            src_addr = struct.unpack('<H', data[6:8])[0]
            
            # Frame type
            frame_type = self.FRAME_TYPES.get((frame_control >> 0) & 0x07, "Unknown")
            
            # Payload
            payload = data[9:]
            
            return AdvancedProtocolFrame(
                protocol=ProtocolType.ZIGBEE,
                timestamp=0.0,
                channel=channel,
                rssi=rssi,
                source_addr=f"0x{src_addr:04X}",
                dest_addr=f"0x{dest_addr:04X}",
                frame_type=frame_type,
                payload=payload,
                metadata={
                    "seq_num": seq_num,
                    "dest_pan_id": f"0x{dest_pan_id:04X}",
                    "frame_control": f"0x{frame_control:02X}",
                }
            )
        except Exception as e:
            logger.debug(f"Zigbee decode error: {e}")
            return None


class ThreadDecoder:
    """Thread (802.15.4-2006 with 6LoWPAN) decoder"""
    
    def decode(self, data: bytes, channel: int = 11, rssi: int = -80) -> Optional[AdvancedProtocolFrame]:
        """Decode Thread frame"""
        if len(data) < 3:
            return None
        
        try:
            # Parse 802.15.4 header
            frame_control = struct.unpack('<H', data[0:2])[0]
            seq_num = data[2]
            
            # Determine addressing mode
            src_mode = (frame_control >> 14) & 0x03
            dest_mode = (frame_control >> 10) & 0x03
            
            offset = 3
            
            # Destination addressing
            dest_addr = "Broadcast"
            if dest_mode == 2:  # Short address
                dest_pan_id = struct.unpack('<H', data[offset:offset+2])[0]
                dest_addr_val = struct.unpack('<H', data[offset+2:offset+4])[0]
                dest_addr = f"0x{dest_addr_val:04X}"
                offset += 4
            
            # Source addressing
            src_addr = "Unknown"
            if src_mode == 2:  # Short address
                src_pan_id = struct.unpack('<H', data[offset:offset+2])[0]
                src_addr_val = struct.unpack('<H', data[offset+2:offset+4])[0]
                src_addr = f"0x{src_addr_val:04X}"
                offset += 4
            
            # Frame type
            frame_type_val = (frame_control >> 0) & 0x07
            frame_types = {0: "Beacon", 1: "Data", 2: "Ack", 3: "MAC Command"}
            frame_type = frame_types.get(frame_type_val, f"Type_{frame_type_val}")
            
            # Check for 6LoWPAN
            payload = data[offset:]
            is_6lowpan = len(payload) > 0 and payload[0] in [0x41, 0x42, 0x60, 0x7B]
            
            return AdvancedProtocolFrame(
                protocol=ProtocolType.THREAD,
                timestamp=0.0,
                channel=channel,
                rssi=rssi,
                source_addr=src_addr,
                dest_addr=dest_addr,
                frame_type=frame_type,
                payload=payload,
                metadata={
                    "seq_num": seq_num,
                    "is_6lowpan": is_6lowpan,
                    "frame_control": f"0x{frame_control:04X}",
                }
            )
        except Exception as e:
            logger.debug(f"Thread decode error: {e}")
            return None


class IEEE802_15_4_Decoder:
    """IEEE 802.15.4 decoder"""
    
    def decode(self, data: bytes, channel: int = 11, rssi: int = -80) -> Optional[AdvancedProtocolFrame]:
        """Decode 802.15.4 frame"""
        if len(data) < 3:
            return None
        
        try:
            frame_control = struct.unpack('<H', data[0:2])[0]
            seq_num = data[2]
            
            # Frame type
            frame_type_val = frame_control & 0x07
            frame_types = {
                0: "Beacon",
                1: "Data", 
                2: "Ack",
                3: "MAC Command",
                4: "Reserved",
                5: "Reserved",
                6: "Reserved",
                7: "Reserved"
            }
            frame_type = frame_types.get(frame_type_val, "Unknown")
            
            # Security enabled
            security = (frame_control >> 3) & 0x01
            
            # Frame pending
            pending = (frame_control >> 4) & 0x01
            
            # AR
            ar = (frame_control >> 5) & 0x01
            
            # Parse addresses if present
            offset = 3
            src_addr = "None"
            dest_addr = "None"
            
            # This is a simplified parser - full implementation would parse all addressing modes
            payload = data[offset:]
            
            return AdvancedProtocolFrame(
                protocol=ProtocolType.IEEE_802_15_4,
                timestamp=0.0,
                channel=channel,
                rssi=rssi,
                source_addr=src_addr,
                dest_addr=dest_addr,
                frame_type=frame_type,
                payload=payload,
                metadata={
                    "seq_num": seq_num,
                    "security": bool(security),
                    "frame_pending": bool(pending),
                    "ack_request": bool(ar),
                }
            )
        except Exception as e:
            logger.debug(f"802.15.4 decode error: {e}")
            return None


class ANTPlusDecoder:
    """ANT+ protocol decoder"""
    
    # ANT+ device types
    DEVICE_TYPES = {
        1: "Heart Rate Monitor",
        2: "Bike Speed Sensor",
        3: "Bike Cadence Sensor",
        4: "Bike Speed/Cadence",
        5: "Power Meter",
        17: "Fitness Equipment",
        18: "Blood Pressure",
        19: "Geocache",
        20: "Weight Scale",
        25: "Environment Sensor",
        40: "Muscle Oxygen",
        119: "Bike Light",
        120: "Bike Light",
        121: "Bike Light",
    }
    
    def decode(self, data: bytes, channel: int = 0, rssi: int = -80) -> Optional[AdvancedProtocolFrame]:
        """Decode ANT+ frame"""
        if len(data) < 13:
            return None
        
        try:
            # ANT+ message structure
            sync = data[0]
            msg_length = data[1]
            msg_id = data[2]
            
            # Channel ID (4 bytes)
            channel_id = struct.unpack('<I', data[3:7])[0]
            device_num = channel_id & 0xFFFF
            device_type = (channel_id >> 16) & 0xFF
            trans_type = (channel_id >> 24) & 0xFF
            
            # Payload
            payload = data[7:7+msg_length]
            
            # Checksum (last byte)
            checksum = data[7+msg_length]
            
            device_name = self.DEVICE_TYPES.get(device_type, f"Unknown({device_type})")
            
            return AdvancedProtocolFrame(
                protocol=ProtocolType.ANT_PLUS,
                timestamp=0.0,
                channel=channel,
                rssi=rssi,
                source_addr=f"Device_{device_num}",
                dest_addr=f"Channel_{channel}",
                frame_type=f"MSG_{msg_id:02X}",
                payload=payload,
                metadata={
                    "device_type": device_type,
                    "device_name": device_name,
                    "trans_type": trans_type,
                    "msg_id": msg_id,
                    "checksum": checksum,
                }
            )
        except Exception as e:
            logger.debug(f"ANT+ decode error: {e}")
            return None


class AdvancedProtocolDecoder:
    """
    Main advanced protocol decoder
    Dispatches to specific decoders based on protocol hints
    """
    
    def __init__(self):
        self.decoders = {
            ProtocolType.ZIGBEE: ZigbeeDecoder(),
            ProtocolType.THREAD: ThreadDecoder(),
            ProtocolType.IEEE_802_15_4: IEEE802_15_4_Decoder(),
            ProtocolType.ANT_PLUS: ANTPlusDecoder(),
        }
        
        logger.info("AdvancedProtocolDecoder initialized")
    
    def decode(self, data: bytes, protocol_hint: Optional[ProtocolType] = None,
               channel: int = 11, rssi: int = -80) -> Optional[AdvancedProtocolFrame]:
        """
        Decode advanced protocol frame
        
        Args:
            data: Raw frame data
            protocol_hint: Optional protocol type hint
            channel: RF channel
            rssi: Signal strength
        
        Returns:
            Decoded frame or None
        """
        if protocol_hint and protocol_hint in self.decoders:
            return self.decoders[protocol_hint].decode(data, channel, rssi)
        
        # Try all decoders
        for protocol, decoder in self.decoders.items():
            try:
                result = decoder.decode(data, channel, rssi)
                if result:
                    return result
            except Exception:
                continue
        
        return None
    
    def detect_protocol(self, data: bytes) -> Optional[ProtocolType]:
        """
        Attempt to detect protocol from frame data
        
        Args:
            data: Raw frame data
        
        Returns:
            Detected protocol type or None
        """
        # Try each decoder
        for protocol, decoder in self.decoders.items():
            try:
                result = decoder.decode(data)
                if result:
                    return protocol
            except Exception:
                continue
        
        return None
    
    def get_supported_protocols(self) -> List[str]:
        """Get list of supported protocol names"""
        return [p.value for p in self.decoders.keys()]


def test_advanced_protocols():
    """Test advanced protocol decoders"""
    print("\n" + "="*60)
    print("Advanced Protocol Decoder Test")
    print("="*60)
    
    decoder = AdvancedProtocolDecoder()
    
    # Test 1: Supported protocols
    print("\n1. Testing supported protocols:")
    protocols = decoder.get_supported_protocols()
    for p in protocols:
        print(f"   {p}")
    
    # Test 2: Zigbee decode
    print("\n2. Testing Zigbee decoder:")
    # Create synthetic Zigbee frame
    zigbee_frame = bytes([
        0x61,  # Frame control (data frame, no security)
        0x01,  # Sequence number
        0xCD, 0xAB,  # Dest PAN ID
        0x34, 0x12,  # Dest short address
        0x78, 0x56,  # Src short address
        0x01, 0x02, 0x03, 0x04,  # Payload
    ])
    
    result = decoder.decode(zigbee_frame, ProtocolType.ZIGBEE)
    if result:
        print(f"   Decoded: {result.frame_type}")
        print(f"    Source: {result.source_addr}")
        print(f"    Dest: {result.dest_addr}")
    else:
        print("   Failed to decode")
    
    # Test 3: Thread decode
    print("\n3. Testing Thread decoder:")
    # Create synthetic Thread frame (802.15.4 with 6LoWPAN)
    thread_frame = bytes([
        0x41, 0xD8,  # Frame control (data, short addresses)
        0x01,  # Sequence
        0xFF, 0xFF,  # Dest PAN (broadcast)
        0xFF, 0xFF,  # Dest addr (broadcast)
        0xCD, 0xAB,  # Src PAN
        0x34, 0x12,  # Src addr
        0x7B, 0x33, 0x00,  # 6LoWPAN header
    ])
    
    result = decoder.decode(thread_frame, ProtocolType.THREAD)
    if result:
        print(f"   Decoded: {result.frame_type}")
        print(f"    6LoWPAN: {result.metadata.get('is_6lowpan', False)}")
    else:
        print("   Failed to decode")
    
    # Test 4: Protocol detection
    print("\n4. Testing protocol detection:")
    detected = decoder.detect_protocol(zigbee_frame)
    print(f"  Detected: {detected.value if detected else 'None'}")
    
    print("\n All advanced protocol tests completed")
    return True


if __name__ == "__main__":
    test_advanced_protocols()
