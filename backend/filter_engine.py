"""
Filter Engine - Advanced filtering and search for BLE data
Provides complex filtering capabilities for devices, packets, and sessions
"""

import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.capture_manager import BLEDevice, BLEPacket
from backend.protocol_parser import ParsedPacket


logger = logging.getLogger(__name__)


class FilterOperator(Enum):
    """Filter operators"""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES = "matches"  # Regex
    IN = "in"
    BETWEEN = "between"


class FilterField(Enum):
    """Filterable fields"""
    # Device fields
    DEVICE_ADDRESS = "device_address"
    DEVICE_NAME = "device_name"
    DEVICE_RSSI = "device_rssi"
    DEVICE_PACKET_COUNT = "device_packet_count"
    DEVICE_FIRST_SEEN = "device_first_seen"
    DEVICE_LAST_SEEN = "device_last_seen"
    DEVICE_MANUFACTURER = "device_manufacturer"
    
    # Packet fields
    PACKET_TYPE = "packet_type"
    PACKET_CHANNEL = "packet_channel"
    PACKET_RSSI = "packet_rssi"
    PACKET_TIMESTAMP = "packet_timestamp"
    PACKET_DATA_LENGTH = "packet_data_length"
    
    # Protocol fields
    PROTOCOL_LL_TYPE = "protocol_ll_type"
    PROTOCOL_L2CAP_CID = "protocol_l2cap_cid"
    PROTOCOL_ATT_OPCODE = "protocol_att_opcode"
    PROTOCOL_GATT_SERVICE = "protocol_gatt_service"
    PROTOCOL_ADV_NAME = "protocol_adv_name"
    PROTOCOL_ADV_UUID = "protocol_adv_uuid"


@dataclass
class FilterCondition:
    """Single filter condition"""
    field: FilterField
    operator: FilterOperator
    value: Any
    value2: Optional[Any] = None  # For BETWEEN operator
    negate: bool = False


@dataclass
class FilterGroup:
    """Group of filter conditions with logic"""
    conditions: List[Union[FilterCondition, 'FilterGroup']]
    operator: str = "AND"  # "AND" or "OR"
    negate: bool = False


class FilterEngine:
    """
    Advanced filtering engine for BLE data
    Supports complex nested filters with AND/OR logic
    """
    
    def __init__(self):
        self.saved_filters: Dict[str, FilterGroup] = {}
        self.filter_history: List[Dict[str, Any]] = []
        
        logger.info("FilterEngine initialized")
    
    def create_condition(self, field: str, operator: str, value: Any,
                        value2: Optional[Any] = None) -> FilterCondition:
        """
        Create a filter condition
        
        Args:
            field: Field name (e.g., 'device_name', 'packet_type')
            operator: Operator (e.g., '==', 'contains', '>')
            value: Value to compare
            value2: Second value for BETWEEN operator
        
        Returns:
            FilterCondition object
        """
        try:
            field_enum = FilterField(field)
        except ValueError:
            raise ValueError(f"Unknown field: {field}")
        
        try:
            op_enum = FilterOperator(operator)
        except ValueError:
            raise ValueError(f"Unknown operator: {operator}")
        
        return FilterCondition(
            field=field_enum,
            operator=op_enum,
            value=value,
            value2=value2
        )
    
    def create_group(self, conditions: List[FilterCondition],
                    operator: str = "AND") -> FilterGroup:
        """Create a filter group"""
        return FilterGroup(
            conditions=conditions,
            operator=operator.upper()
        )
    
    def filter_devices(self, devices: List[BLEDevice],
                      filter_group: FilterGroup) -> List[BLEDevice]:
        """
        Filter devices based on filter group
        
        Args:
            devices: List of BLEDevice objects
            filter_group: FilterGroup with conditions
        
        Returns:
            Filtered list of devices
        """
        return [d for d in devices if self._evaluate_device(d, filter_group)]
    
    def filter_packets(self, packets: List[BLEPacket],
                      filter_group: FilterGroup) -> List[BLEPacket]:
        """
        Filter packets based on filter group
        
        Args:
            packets: List of BLEPacket objects
            filter_group: FilterGroup with conditions
        
        Returns:
            Filtered list of packets
        """
        return [p for p in packets if self._evaluate_packet(p, filter_group)]
    
    def filter_parsed_packets(self, packets: List[ParsedPacket],
                             filter_group: FilterGroup) -> List[ParsedPacket]:
        """
        Filter parsed packets based on filter group
        
        Args:
            packets: List of ParsedPacket objects
            filter_group: FilterGroup with conditions
        
        Returns:
            Filtered list of parsed packets
        """
        return [p for p in packets if self._evaluate_parsed_packet(p, filter_group)]
    
    def _evaluate_device(self, device: BLEDevice, group: FilterGroup) -> bool:
        """Evaluate filter group against a device"""
        results = []
        
        for condition in group.conditions:
            if isinstance(condition, FilterGroup):
                result = self._evaluate_device(device, condition)
            else:
                result = self._evaluate_device_condition(device, condition)
            
            results.append(result)
        
        # Apply logic
        if group.operator == "AND":
            final_result = all(results)
        else:  # OR
            final_result = any(results)
        
        if group.negate:
            final_result = not final_result
        
        return final_result
    
    def _evaluate_device_condition(self, device: BLEDevice,
                                   condition: FilterCondition) -> bool:
        """Evaluate single condition against a device"""
        field = condition.field
        op = condition.operator
        value = condition.value
        
        # Get field value
        if field == FilterField.DEVICE_ADDRESS:
            field_value = device.address
        elif field == FilterField.DEVICE_NAME:
            field_value = device.name
        elif field == FilterField.DEVICE_RSSI:
            field_value = device.rssi
        elif field == FilterField.DEVICE_PACKET_COUNT:
            field_value = device.packet_count
        elif field == FilterField.DEVICE_FIRST_SEEN:
            field_value = device.first_seen
        elif field == FilterField.DEVICE_LAST_SEEN:
            field_value = device.last_seen
        elif field == FilterField.DEVICE_MANUFACTURER:
            # Extract manufacturer from manufacturer_data
            field_value = ""
            if device.manufacturer_data:
                # First key is usually manufacturer ID
                field_value = str(list(device.manufacturer_data.keys())[0])
        else:
            return False
        
        result = self._compare_values(field_value, op, value, condition.value2)
        
        if condition.negate:
            result = not result
        
        return result
    
    def _evaluate_packet(self, packet: BLEPacket, group: FilterGroup) -> bool:
        """Evaluate filter group against a packet"""
        results = []
        
        for condition in group.conditions:
            if isinstance(condition, FilterGroup):
                result = self._evaluate_packet(packet, condition)
            else:
                result = self._evaluate_packet_condition(packet, condition)
            
            results.append(result)
        
        if group.operator == "AND":
            final_result = all(results)
        else:
            final_result = any(results)
        
        if group.negate:
            final_result = not final_result
        
        return final_result
    
    def _evaluate_packet_condition(self, packet: BLEPacket,
                                  condition: FilterCondition) -> bool:
        """Evaluate single condition against a packet"""
        field = condition.field
        op = condition.operator
        value = condition.value
        
        # Get field value
        if field == FilterField.PACKET_TYPE:
            field_value = packet.packet_type
        elif field == FilterField.PACKET_CHANNEL:
            field_value = packet.channel
        elif field == FilterField.PACKET_RSSI:
            field_value = packet.rssi
        elif field == FilterField.PACKET_TIMESTAMP:
            field_value = packet.timestamp
        elif field == FilterField.PACKET_DATA_LENGTH:
            field_value = len(packet.data)
        elif field == FilterField.DEVICE_ADDRESS:
            field_value = packet.device_address
        else:
            return False
        
        result = self._compare_values(field_value, op, value, condition.value2)
        
        if condition.negate:
            result = not result
        
        return result
    
    def _evaluate_parsed_packet(self, packet: ParsedPacket,
                              group: FilterGroup) -> bool:
        """Evaluate filter group against a parsed packet"""
        results = []
        
        for condition in group.conditions:
            if isinstance(condition, FilterGroup):
                result = self._evaluate_parsed_packet(packet, condition)
            else:
                result = self._evaluate_parsed_condition(packet, condition)
            
            results.append(result)
        
        if group.operator == "AND":
            final_result = all(results)
        else:
            final_result = any(results)
        
        if group.negate:
            final_result = not final_result
        
        return final_result
    
    def _evaluate_parsed_condition(self, packet: ParsedPacket,
                                 condition: FilterCondition) -> bool:
        """Evaluate single condition against a parsed packet"""
        field = condition.field
        op = condition.operator
        value = condition.value
        
        # Get field value from parsed packet
        field_map = {
            FilterField.PROTOCOL_LL_TYPE: packet.ll_type,
            FilterField.PROTOCOL_L2CAP_CID: packet.l2cap_cid,
            FilterField.PROTOCOL_ATT_OPCODE: packet.att_opcode,
            FilterField.PROTOCOL_GATT_SERVICE: packet.gatt_service_uuid,
            FilterField.PROTOCOL_ADV_NAME: packet.adv_local_name,
            FilterField.PROTOCOL_ADV_UUID: packet.adv_service_uuids[0] if packet.adv_service_uuids else "",
            FilterField.PACKET_CHANNEL: packet.channel,
            FilterField.PACKET_RSSI: packet.rssi,
        }
        
        field_value = field_map.get(field)
        
        if field_value is None:
            return False
        
        result = self._compare_values(field_value, op, value, condition.value2)
        
        if condition.negate:
            result = not result
        
        return result
    
    def _compare_values(self, field_value: Any, op: FilterOperator,
                       value: Any, value2: Optional[Any] = None) -> bool:
        """Compare field value with condition value"""
        try:
            if op == FilterOperator.EQUALS:
                return field_value == value
            
            elif op == FilterOperator.NOT_EQUALS:
                return field_value != value
            
            elif op == FilterOperator.GREATER_THAN:
                return field_value > value
            
            elif op == FilterOperator.LESS_THAN:
                return field_value < value
            
            elif op == FilterOperator.GREATER_EQUAL:
                return field_value >= value
            
            elif op == FilterOperator.LESS_EQUAL:
                return field_value <= value
            
            elif op == FilterOperator.CONTAINS:
                if isinstance(field_value, str):
                    return value.lower() in field_value.lower()
                elif isinstance(field_value, (list, bytes)):
                    return value in field_value
                return False
            
            elif op == FilterOperator.STARTS_WITH:
                if isinstance(field_value, str):
                    return field_value.lower().startswith(value.lower())
                return False
            
            elif op == FilterOperator.ENDS_WITH:
                if isinstance(field_value, str):
                    return field_value.lower().endswith(value.lower())
                return False
            
            elif op == FilterOperator.MATCHES:
                if isinstance(field_value, str):
                    return bool(re.search(value, field_value, re.IGNORECASE))
                return False
            
            elif op == FilterOperator.IN:
                return field_value in value
            
            elif op == FilterOperator.BETWEEN:
                if value2 is not None:
                    return value <= field_value <= value2
                return False
            
            return False
            
        except Exception as e:
            logger.debug(f"Comparison error: {e}")
            return False
    
    def quick_search(self, devices: List[BLEDevice],
                    search_term: str) -> List[BLEDevice]:
        """
        Quick search across device fields
        
        Args:
            devices: List of devices
            search_term: Search string
        
        Returns:
            Matching devices
        """
        search_lower = search_term.lower()
        
        results = []
        for device in devices:
            # Search in name
            if search_lower in device.name.lower():
                results.append(device)
                continue
            
            # Search in address
            if search_lower in device.address.lower():
                results.append(device)
                continue
            
            # Search in service UUIDs
            for uuid in device.service_uuids:
                if search_lower in uuid.lower():
                    results.append(device)
                    break
        
        return results
    
    def save_filter(self, name: str, filter_group: FilterGroup):
        """Save a filter for later use"""
        self.saved_filters[name] = filter_group
        logger.info(f"Saved filter: {name}")
    
    def load_filter(self, name: str) -> Optional[FilterGroup]:
        """Load a saved filter"""
        return self.saved_filters.get(name)
    
    def get_saved_filters(self) -> List[str]:
        """Get list of saved filter names"""
        return list(self.saved_filters.keys())
    
    def delete_filter(self, name: str) -> bool:
        """Delete a saved filter"""
        if name in self.saved_filters:
            del self.saved_filters[name]
            logger.info(f"Deleted filter: {name}")
            return True
        return False
    
    def get_filter_history(self) -> List[Dict[str, Any]]:
        """Get filter usage history"""
        return self.filter_history


# Global filter engine instance
_filter_engine: Optional[FilterEngine] = None


def get_filter_engine() -> FilterEngine:
    """Get or create global filter engine instance"""
    global _filter_engine
    if _filter_engine is None:
        _filter_engine = FilterEngine()
    return _filter_engine


def test_filter_engine():
    """Test filter engine functionality"""
    print("\n" + "="*60)
    print("Filter Engine Test")
    print("="*60)
    
    from backend.capture_manager import BLEDevice, BLEPacket
    from datetime import datetime
    
    engine = get_filter_engine()
    
    # Create test devices
    devices = [
        BLEDevice(address="AA:BB:CC:DD:EE:01", name="iPhone 12", rssi=-65, packet_count=100),
        BLEDevice(address="AA:BB:CC:DD:EE:02", name="Samsung Galaxy", rssi=-72, packet_count=50),
        BLEDevice(address="AA:BB:CC:DD:EE:03", name="Fitbit Charge", rssi=-80, packet_count=200),
        BLEDevice(address="AA:BB:CC:DD:EE:04", name="AirPods Pro", rssi=-55, packet_count=30),
    ]
    
    # Test 1: Simple filter
    print("\n1. Testing RSSI filter (RSSI > -70):")
    condition = engine.create_condition("device_rssi", ">", -70)
    group = engine.create_group([condition])
    
    filtered = engine.filter_devices(devices, group)
    print(f"  Filtered {len(devices)} devices -> {len(filtered)} devices")
    for d in filtered:
        print(f"    - {d.name}: RSSI {d.rssi}")
    
    # Test 2: Name contains filter
    print("\n2. Testing name filter (contains 'Pro'):")
    condition = engine.create_condition("device_name", "contains", "Pro")
    group = engine.create_group([condition])
    
    filtered = engine.filter_devices(devices, group)
    print(f"  Found {len(filtered)} devices:")
    for d in filtered:
        print(f"    - {d.name}")
    
    # Test 3: Quick search
    print("\n3. Testing quick search ('Phone'):")
    results = engine.quick_search(devices, "Phone")
    print(f"  Found {len(results)} devices:")
    for d in results:
        print(f"    - {d.name}")
    
    # Test 4: Complex filter (AND)
    print("\n4. Testing complex filter (RSSI > -75 AND packets > 40):")
    condition1 = engine.create_condition("device_rssi", ">", -75)
    condition2 = engine.create_condition("device_packet_count", ">", 40)
    group = engine.create_group([condition1, condition2], "AND")
    
    filtered = engine.filter_devices(devices, group)
    print(f"  Filtered to {len(filtered)} devices:")
    for d in filtered:
        print(f"    - {d.name}: RSSI {d.rssi}, Packets {d.packet_count}")
    
    # Test 5: Save and load filter
    print("\n5. Testing save/load filter:")
    engine.save_filter("strong_signal", group)
    loaded = engine.load_filter("strong_signal")
    print(f"  Saved and loaded filter 'strong_signal': {loaded is not None}")
    
    return True


if __name__ == "__main__":
    result = test_filter_engine()
    print(f"\nTest {'PASSED' if result else 'FAILED'}")
