"""
Protocol Parser - BLE Protocol Stack Parser
Parses BLE protocols: L2CAP, ATT, GATT, GAP
"""

import struct
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import IntEnum

logger = logging.getLogger(__name__)


class BLEPDUType(IntEnum):
    """BLE PDU Types"""
    ADV_IND = 0x00
    ADV_DIRECT_IND = 0x01
    ADV_NONCONN_IND = 0x02
    SCAN_REQ = 0x03
    SCAN_RSP = 0x04
    CONNECT_REQ = 0x05
    ADV_SCAN_IND = 0x06


class L2CAPCode(IntEnum):
    """L2CAP Command Codes"""
    COMMAND_REJECT = 0x01
    DISCONNECTION_REQUEST = 0x06
    DISCONNECTION_RESPONSE = 0x07
    CONNECTION_PARAMETER_UPDATE_REQUEST = 0x12
    CONNECTION_PARAMETER_UPDATE_RESPONSE = 0x13
    LE_CREDIT_BASED_CONNECTION_REQUEST = 0x14
    LE_CREDIT_BASED_CONNECTION_RESPONSE = 0x15
    FLOW_CONTROL_CREDIT_IND = 0x16
    CREDIT_BASED_CONNECTION_REQUEST = 0x17
    CREDIT_BASED_CONNECTION_RESPONSE = 0x18
    CREDIT_BASED_RECONFIGURE_REQUEST = 0x19
    CREDIT_BASED_RECONFIGURE_RESPONSE = 0x1A


class ATTOpcode(IntEnum):
    """ATT Protocol Opcodes"""
    ERROR_RESPONSE = 0x01
    EXCHANGE_MTU_REQUEST = 0x02
    EXCHANGE_MTU_RESPONSE = 0x03
    FIND_INFORMATION_REQUEST = 0x04
    FIND_INFORMATION_RESPONSE = 0x05
    FIND_BY_TYPE_VALUE_REQUEST = 0x06
    FIND_BY_TYPE_VALUE_RESPONSE = 0x07
    READ_BY_TYPE_REQUEST = 0x08
    READ_BY_TYPE_RESPONSE = 0x09
    READ_REQUEST = 0x0A
    READ_RESPONSE = 0x0B
    READ_BLOB_REQUEST = 0x0C
    READ_BLOB_RESPONSE = 0x0D
    READ_MULTIPLE_REQUEST = 0x0E
    READ_MULTIPLE_RESPONSE = 0x0F
    READ_BY_GROUP_TYPE_REQUEST = 0x10
    READ_BY_GROUP_TYPE_RESPONSE = 0x11
    WRITE_REQUEST = 0x12
    WRITE_RESPONSE = 0x13
    WRITE_COMMAND = 0x52
    PREPARE_WRITE_REQUEST = 0x16
    PREPARE_WRITE_RESPONSE = 0x17
    EXECUTE_WRITE_REQUEST = 0x18
    EXECUTE_WRITE_RESPONSE = 0x19
    READ_MULTIPLE_VARIABLE_REQUEST = 0x20
    READ_MULTIPLE_VARIABLE_RESPONSE = 0x21
    MULTIPLE_HANDLE_VALUE_NOTIFICATION = 0x23
    HANDLE_VALUE_NOTIFICATION = 0x1B
    HANDLE_VALUE_INDICATION = 0x1D
    HANDLE_VALUE_CONFIRMATION = 0x1E
    SIGNED_WRITE_COMMAND = 0xD2


@dataclass
class ParsedPacket:
    """Parsed BLE packet with all protocol layers"""
    raw_data: bytes
    timestamp: float
    rssi: int
    channel: int
    
    # Link Layer
    ll_type: str = ""
    ll_address: str = ""
    ll_length: int = 0
    
    # L2CAP
    l2cap_length: int = 0
    l2cap_cid: int = 0
    l2cap_code: Optional[int] = None
    l2cap_data: bytes = field(default_factory=bytes)
    
    # ATT
    att_opcode: Optional[int] = None
    att_opcode_name: str = ""
    att_handle: Optional[int] = None
    att_value: bytes = field(default_factory=bytes)
    
    # GATT
    gatt_service_uuid: str = ""
    gatt_characteristic_uuid: str = ""
    gatt_operation: str = ""
    
    # Advertising Data
    adv_flags: int = 0
    adv_local_name: str = ""
    adv_tx_power: Optional[int] = None
    adv_manufacturer_data: bytes = field(default_factory=bytes)
    adv_service_uuids: List[str] = field(default_factory=list)
    
    # Parsed summary
    summary: str = ""
    protocol_stack: List[str] = field(default_factory=list)


class ProtocolParser:
    """
    BLE Protocol Stack Parser
    Parses Link Layer, L2CAP, ATT, GATT protocols
    """
    
    def __init__(self):
        self.parsed_count = 0
        self.error_count = 0
        
        # UUID name mappings
        self.uuid_names = {
            '00001800-0000-1000-8000-00805f9b34fb': 'Generic Access',
            '00001801-0000-1000-8000-00805f9b34fb': 'Generic Attribute',
            '0000180a-0000-1000-8000-00805f9b34fb': 'Device Information',
            '0000180f-0000-1000-8000-00805f9b34fb': 'Battery Service',
            '00001812-0000-1000-8000-00805f9b34fb': 'HID Service',
            '00002a00-0000-1000-8000-00805f9b34fb': 'Device Name',
            '00002a01-0000-1000-8000-00805f9b34fb': 'Appearance',
            '00002a19-0000-1000-8000-00805f9b34fb': 'Battery Level',
            '00002a29-0000-1000-8000-00805f9b34fb': 'Manufacturer Name',
            '00002a50-0000-1000-8000-00805f9b34fb': 'PnP ID',
        }
        
        logger.info("ProtocolParser initialized")
    
    def parse_packet(self, data: bytes, timestamp: float = 0.0, 
                     rssi: int = 0, channel: int = 37) -> ParsedPacket:
        """
        Parse a BLE packet through all protocol layers
        
        Args:
            data: Raw packet data
            timestamp: Packet timestamp
            rssi: Signal strength
            channel: BLE channel
        
        Returns:
            ParsedPacket with all protocol layers decoded
        """
        try:
            packet = ParsedPacket(
                raw_data=data,
                timestamp=timestamp,
                rssi=rssi,
                channel=channel,
                ll_length=len(data)
            )
            
            # Parse Link Layer (Advertising or Data)
            if len(data) >= 2:
                self._parse_link_layer(packet, data)
                
                # Parse L2CAP if data packet
                if packet.ll_type in ['DATA'] and len(data) > 4:
                    self._parse_l2cap(packet, data[2:])
                    
                    # Parse ATT if L2CAP CID is ATT
                    if packet.l2cap_cid == 0x0004:  # ATT CID
                        self._parse_att(packet, packet.l2cap_data)
                
                # Parse Advertising Data
                elif packet.ll_type in ['ADV_IND', 'SCAN_RSP', 'ADV_NONCONN_IND']:
                    self._parse_advertising_data(packet, data[2:])
            
            # Generate summary
            self._generate_summary(packet)
            
            self.parsed_count += 1
            return packet
            
        except Exception as e:
            logger.error(f"Error parsing packet: {e}")
            self.error_count += 1
            return ParsedPacket(
                raw_data=data,
                timestamp=timestamp,
                rssi=rssi,
                channel=channel,
                summary=f"Parse Error: {e}"
            )
    
    def _parse_link_layer(self, packet: ParsedPacket, data: bytes):
        """Parse Link Layer header"""
        if len(data) < 2:
            return
        
        # First byte: PDU Type (4 bits) + RFU (2 bits) + ChSel (1 bit) + TxAdd (1 bit)
        header = data[0]
        pdu_type = header & 0x0F
        
        # Map PDU type to name
        pdu_names = {
            0x00: 'ADV_IND',
            0x01: 'ADV_DIRECT_IND',
            0x02: 'ADV_NONCONN_IND',
            0x03: 'SCAN_REQ',
            0x04: 'SCAN_RSP',
            0x05: 'CONNECT_REQ',
            0x06: 'ADV_SCAN_IND',
        }
        
        packet.ll_type = pdu_names.get(pdu_type, f'UNKNOWN({pdu_type})')
        packet.protocol_stack.append(f"LL: {packet.ll_type}")
        
        # Length
        if len(data) > 1:
            packet.ll_length = data[1]
    
    def _parse_l2cap(self, packet: ParsedPacket, data: bytes):
        """Parse L2CAP layer"""
        if len(data) < 4:
            return
        
        # L2CAP Basic Header
        packet.l2cap_length = struct.unpack('<H', data[0:2])[0]
        packet.l2cap_cid = struct.unpack('<H', data[2:4])[0]
        
        packet.protocol_stack.append(f"L2CAP: CID={packet.l2cap_cid:04X}")
        
        # L2CAP payload
        if len(data) > 4:
            packet.l2cap_data = data[4:4+packet.l2cap_length]
        
        # Check for L2CAP signaling channel
        if packet.l2cap_cid == 0x0005 and len(packet.l2cap_data) > 0:
            packet.l2cap_code = packet.l2cap_data[0]
            code_name = L2CAPCode(packet.l2cap_code).name if packet.l2cap_code in [c.value for c in L2CAPCode] else f"UNKNOWN({packet.l2cap_code})"
            packet.protocol_stack.append(f"L2CAP Signaling: {code_name}")
    
    def _parse_att(self, packet: ParsedPacket, data: bytes):
        """Parse ATT protocol"""
        if len(data) < 1:
            return
        
        packet.att_opcode = data[0]
        
        # Get opcode name
        if packet.att_opcode in [op.value for op in ATTOpcode]:
            packet.att_opcode_name = ATTOpcode(packet.att_opcode).name
        else:
            packet.att_opcode_name = f"UNKNOWN({packet.att_opcode:02X})"
        
        packet.protocol_stack.append(f"ATT: {packet.att_opcode_name}")
        
        # Parse based on opcode
        if packet.att_opcode in [ATTOpcode.READ_REQUEST.value, ATTOpcode.WRITE_REQUEST.value]:
            if len(data) >= 3:
                packet.att_handle = struct.unpack('<H', data[1:3])[0]
        
        elif packet.att_opcode in [ATTOpcode.READ_RESPONSE.value, ATTOpcode.WRITE_COMMAND.value]:
            packet.att_value = data[1:]
        
        elif packet.att_opcode == ATTOpcode.HANDLE_VALUE_NOTIFICATION.value:
            if len(data) >= 3:
                packet.att_handle = struct.unpack('<H', data[1:3])[0]
                packet.att_value = data[3:]
        
        # Determine GATT operation
        packet.gatt_operation = self._get_gatt_operation(packet.att_opcode_name)
    
    def _parse_advertising_data(self, packet: ParsedPacket, data: bytes):
        """Parse advertising data (AD structures)"""
        offset = 0
        
        while offset < len(data):
            length = data[offset]
            if length == 0 or offset + length >= len(data):
                break
            
            ad_type = data[offset + 1]
            ad_data = data[offset + 2:offset + 1 + length]
            
            # Parse AD type
            if ad_type == 0x01:  # Flags
                packet.adv_flags = ad_data[0] if ad_data else 0
            
            elif ad_type == 0x08 or ad_type == 0x09:  # Short/Complete Local Name
                try:
                    packet.adv_local_name = ad_data.decode('utf-8', errors='replace')
                except:
                    packet.adv_local_name = ad_data.hex()
            
            elif ad_type == 0x0A:  # TX Power Level
                packet.adv_tx_power = int.from_bytes(ad_data, 'little', signed=True) if ad_data else None
            
            elif ad_type == 0xFF:  # Manufacturer Specific Data
                packet.adv_manufacturer_data = ad_data
            
            elif ad_type in [0x02, 0x03, 0x06, 0x07]:  # Service UUIDs
                uuid = self._parse_uuid(ad_data)
                if uuid:
                    packet.adv_service_uuids.append(uuid)
            
            offset += 1 + length
    
    def _parse_uuid(self, data: bytes) -> str:
        """Parse UUID from bytes"""
        if len(data) == 2:
            return f"0000{data.hex()}-0000-1000-8000-00805f9b34fb"
        elif len(data) == 4:
            return f"{data.hex()}-0000-1000-8000-00805f9b34fb"
        elif len(data) == 16:
            return f"{data[0:4].hex()}-{data[4:6].hex()}-{data[6:8].hex()}-{data[8:10].hex()}-{data[10:16].hex()}"
        return ""
    
    def _get_gatt_operation(self, opcode_name: str) -> str:
        """Map ATT opcode to GATT operation"""
        if 'READ' in opcode_name:
            return 'Read'
        elif 'WRITE' in opcode_name:
            return 'Write'
        elif 'NOTIFICATION' in opcode_name:
            return 'Notification'
        elif 'INDICATION' in opcode_name:
            return 'Indication'
        elif 'MTU' in opcode_name:
            return 'MTU Exchange'
        elif 'FIND' in opcode_name:
            return 'Discovery'
        else:
            return 'Other'
    
    def _generate_summary(self, packet: ParsedPacket):
        """Generate human-readable summary"""
        parts = []
        
        # Link Layer
        if packet.ll_type:
            parts.append(f"{packet.ll_type}")
        
        # Advertising info
        if packet.adv_local_name:
            parts.append(f"Name: {packet.adv_local_name}")
        
        if packet.adv_service_uuids:
            service_names = [self.uuid_names.get(uuid, uuid[:8]) for uuid in packet.adv_service_uuids[:2]]
            parts.append(f"Services: {', '.join(service_names)}")
        
        # ATT info
        if packet.att_opcode_name:
            parts.append(f"ATT: {packet.att_opcode_name}")
            if packet.att_handle is not None:
                parts.append(f"Handle: 0x{packet.att_handle:04X}")
        
        # L2CAP info
        if packet.l2cap_cid and packet.l2cap_cid != 0x0004:
            parts.append(f"L2CAP CID: 0x{packet.l2cap_cid:04X}")
        
        packet.summary = " | ".join(parts) if parts else "Unknown Packet"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parser statistics"""
        return {
            'parsed_count': self.parsed_count,
            'error_count': self.error_count,
            'success_rate': (self.parsed_count - self.error_count) / max(self.parsed_count, 1) * 100
        }


# Global parser instance
_parser: Optional[ProtocolParser] = None


def get_protocol_parser() -> ProtocolParser:
    """Get or create global protocol parser instance"""
    global _parser
    if _parser is None:
        _parser = ProtocolParser()
    return _parser


def test_protocol_parser():
    """Test protocol parser with sample data"""
    print("\n" + "="*60)
    print("Protocol Parser Test")
    print("="*60)
    
    parser = get_protocol_parser()
    
    # Test advertising packet with proper Link Layer header
    print("\n1. Testing Advertising Packet:")
    # Link Layer header: PDU type 0x00 (ADV_IND), length
    ll_header = bytes([0x00, 0x15])  # ADV_IND, length=21
    adv_data = bytes([
        0x02, 0x01, 0x06,  # Flags: LE General Discoverable
        0x0A, 0x09, 0x54, 0x65, 0x73, 0x74, 0x20, 0x44, 0x65, 0x76, 0x69, 0x63, 0x65,  # Name: "Test Device"
        0x03, 0x03, 0xAA, 0xFE,  # Service UUID: 0xFEAA (Eddystone)
        0x02, 0x0A, 0xEC,  # TX Power: -20 dBm (0xEC as signed byte)
    ])
    
    full_adv_packet = ll_header + adv_data
    
    packet = parser.parse_packet(full_adv_packet, timestamp=0.0, rssi=-65, channel=37)
    print(f"  Type: {packet.ll_type}")
    print(f"  Name: {packet.adv_local_name}")
    print(f"  Services: {packet.adv_service_uuids}")
    print(f"  TX Power: {packet.adv_tx_power} dBm" if packet.adv_tx_power is not None else "  TX Power: None")
    print(f"  Summary: {packet.summary}")
    
    # Test ATT packet with proper Link Layer header
    print("\n2. Testing ATT Read Request:")
    att_data = bytes([
        0x0A,  # Read Request opcode
        0x03, 0x00,  # Handle: 0x0003
    ])
    
    # Wrap in L2CAP
    l2cap_header = struct.pack('<HH', len(att_data), 0x0004)  # Length + ATT CID
    l2cap_payload = l2cap_header + att_data
    
    # Add Link Layer header for DATA packet
    ll_header = bytes([0x02, len(l2cap_payload)])  # DATA packet type
    full_packet = ll_header + l2cap_payload
    
    packet = parser.parse_packet(full_packet, timestamp=1.0, rssi=-70, channel=0)
    print(f"  Type: {packet.ll_type}")
    print(f"  L2CAP CID: 0x{packet.l2cap_cid:04X}")
    print(f"  ATT Opcode: {packet.att_opcode_name}")
    handle_str = f"0x{packet.att_handle:04X}" if packet.att_handle else "None"
    print(f"  Handle: {handle_str}")
    print(f"  Summary: {packet.summary}")
    
    # Test statistics
    print("\n3. Parser Statistics:")
    stats = parser.get_statistics()
    print(f"  Parsed: {stats['parsed_count']}")
    print(f"  Errors: {stats['error_count']}")
    print(f"  Success Rate: {stats['success_rate']:.1f}%")
    
    return stats['parsed_count'] > 0



if __name__ == "__main__":
    result = test_protocol_parser()
    print(f"\nTest {'PASSED' if result else 'FAILED'}")
