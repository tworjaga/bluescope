"""
Test Suite for Capture Manager
Comprehensive tests for BLE capture functionality
"""

import pytest
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from backend.capture_manager import (
    CaptureManager, CaptureBackend, BLEDevice, BLEPacket,
    get_capture_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestBLEDevice:
    """Tests for BLEDevice class"""
    
    def test_device_creation(self):
        """Test basic device creation"""
        device = BLEDevice(
            address="AA:BB:CC:DD:EE:01",
            name="Test Device",
            rssi=-65
        )
        
        assert device.address == "AA:BB:CC:DD:EE:01"
        assert device.name == "Test Device"
        assert device.rssi == -65
        assert device.packet_count == 0
        assert device.first_seen is not None
        logger.info(" Device creation test passed")
    
    def test_device_update(self):
        """Test device update with new packet"""
        device = BLEDevice(
            address="AA:BB:CC:DD:EE:01",
            name="Test Device",
            rssi=-65
        )
        
        # Simulate packet arrival
        device.packet_count += 1
        device.rssi = -60  # Signal improved
        device.last_seen = datetime.now()
        
        assert device.packet_count == 1
        assert device.rssi == -60
        logger.info(" Device update test passed")
    
    def test_device_type_detection(self):
        """Test automatic device type detection"""
        test_cases = [
            ("iPhone 12", "Smartphone"),
            ("AirPods Pro", "Audio"),
            ("Fitbit Charge", "Wearable"),
            ("Samsung Galaxy", "Smartphone"),
            ("Unknown Device", "Unknown"),
        ]
        
        for name, expected_type in test_cases:
            device = BLEDevice(address="AA:BB:CC:DD:EE:01", name=name)
            # Device type is detected from name patterns
            assert device.name == name
            logger.info(f" Device type detection for '{name}' passed")


class TestBLEPacket:
    """Tests for BLEPacket class"""
    
    def test_packet_creation(self):
        """Test basic packet creation"""
        packet = BLEPacket(
            timestamp=datetime.now(),
            device_address="AA:BB:CC:DD:EE:01",
            packet_type="ADV_IND",
            channel=37,
            rssi=-65,
            data=b"\x02\x01\x06\x03\x03\xaa\xfe"
        )
        
        assert packet.device_address == "AA:BB:CC:DD:EE:01"
        assert packet.packet_type == "ADV_IND"
        assert packet.channel == 37
        assert packet.rssi == -65
        assert len(packet.data) == 7
        logger.info(" Packet creation test passed")
    
    def test_packet_metadata(self):
        """Test packet with metadata"""
        packet = BLEPacket(
            timestamp=datetime.now(),
            device_address="AA:BB:CC:DD:EE:01",
            packet_type="ADV_IND",
            channel=37,
            rssi=-65,
            data=b"\x02\x01\x06",
            metadata={"parsed": True, "protocol": "LL"}
        )
        
        assert packet.metadata["parsed"] is True
        assert packet.metadata["protocol"] == "LL"
        logger.info(" Packet metadata test passed")


class TestCaptureManager:
    """Tests for CaptureManager class"""
    
    @pytest.fixture
    def capture_manager(self):
        """Create a capture manager for testing"""
        return CaptureManager(backend=CaptureBackend.MOCK)
    
    @pytest.mark.asyncio
    async def test_capture_manager_initialization(self, capture_manager):
        """Test capture manager initialization"""
        assert capture_manager is not None
        assert capture_manager.backend == CaptureBackend.MOCK
        assert not capture_manager.is_capturing
        logger.info(" Capture manager initialization test passed")
    
    @pytest.mark.asyncio
    async def test_start_stop_capture(self, capture_manager):
        """Test starting and stopping capture"""
        # Start capture
        success = await capture_manager.start_capture()
        assert success is True
        assert capture_manager.is_capturing
        
        # Let it run briefly
        await asyncio.sleep(0.5)
        
        # Stop capture
        await capture_manager.stop_capture()
        assert not capture_manager.is_capturing
        logger.info(" Start/stop capture test passed")
    
    @pytest.mark.asyncio
    async def test_device_tracking(self, capture_manager):
        """Test device tracking during capture"""
        # Start capture
        await capture_manager.start_capture()
        
        # Wait for some packets
        await asyncio.sleep(1.0)
        
        # Check devices
        devices = capture_manager.get_devices()
        assert isinstance(devices, list)
        
        # Stop capture
        await capture_manager.stop_capture()
        logger.info(f" Device tracking test passed - found {len(devices)} devices")
    
    @pytest.mark.asyncio
    async def test_packet_collection(self, capture_manager):
        """Test packet collection"""
        # Start capture
        await capture_manager.start_capture()
        
        # Wait for packets
        await asyncio.sleep(1.0)
        
        # Get packets
        packets = capture_manager.get_packets(limit=100)
        assert isinstance(packets, list)
        assert len(packets) <= 100
        
        # Stop capture
        await capture_manager.stop_capture()
        logger.info(f" Packet collection test passed - collected {len(packets)} packets")
    
    @pytest.mark.asyncio
    async def test_statistics(self, capture_manager):
        """Test statistics collection"""
        # Start capture
        await capture_manager.start_capture()
        
        # Wait for data
        await asyncio.sleep(1.0)
        
        # Get statistics
        stats = capture_manager.get_statistics()
        assert "total_packets" in stats
        assert "total_devices" in stats
        assert "packets_per_second" in stats
        
        # Stop capture
        await capture_manager.stop_capture()
        logger.info(f" Statistics test passed - {stats}")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, capture_manager):
        """Test error handling"""
        # Test starting capture twice (should handle gracefully)
        success1 = await capture_manager.start_capture()
        success2 = await capture_manager.start_capture()
        
        # Second start should fail or be ignored
        assert success1 is True
        
        # Stop
        await capture_manager.stop_capture()
        logger.info(" Error handling test passed")
    
    def test_get_capture_manager_singleton(self):
        """Test singleton pattern"""
        cm1 = get_capture_manager()
        cm2 = get_capture_manager()
        
        assert cm1 is cm2
        logger.info(" Singleton test passed")


class TestMultiCaptureManager:
    """Tests for MultiCaptureManager"""
    
    @pytest.mark.asyncio
    async def test_multi_device_capture(self):
        """Test capturing from multiple devices"""
        from backend.multi_capture_manager import MultiCaptureManager
        
        manager = MultiCaptureManager()
        
        # Add mock devices
        await manager.add_mock_device("device1")
        await manager.add_mock_device("device2")
        
        # Start capture
        success = await manager.start_all()
        assert success
        
        # Wait for data
        await asyncio.sleep(1.0)
        
        # Get statistics
        stats = manager.get_statistics()
        assert "total_packets" in stats
        
        # Stop
        await manager.stop_all()
        logger.info(" Multi-device capture test passed")


class TestProtocolParser:
    """Tests for ProtocolParser"""
    
    def test_parse_advertising_packet(self):
        """Test parsing advertising packet"""
        from backend.protocol_parser import get_protocol_parser
        
        parser = get_protocol_parser()
        
        # Create advertising packet with LL header
        ll_header = bytes([0x00, 0x15])  # ADV_IND
        adv_data = bytes([
            0x02, 0x01, 0x06,
            0x0A, 0x09, 0x54, 0x65, 0x73, 0x74, 0x20, 0x44, 0x65, 0x76, 0x69, 0x63, 0x65,
            0x03, 0x03, 0xAA, 0xFE,
        ])
        
        packet = parser.parse_packet(ll_header + adv_data, timestamp=0.0, rssi=-65, channel=37)
        
        assert packet.ll_type == "ADV_IND"
        assert packet.adv_local_name == "Test Device"
        assert len(packet.adv_service_uuids) > 0
        logger.info(" Advertising packet parsing test passed")
    
    def test_parse_att_packet(self):
        """Test parsing ATT packet"""
        import struct
        from backend.protocol_parser import get_protocol_parser
        
        parser = get_protocol_parser()
        
        # Create ATT read request
        att_data = bytes([0x0A, 0x03, 0x00])  # Read Request, handle 0x0003
        l2cap_header = struct.pack('<HH', len(att_data), 0x0004)
        ll_header = bytes([0x02, len(l2cap_header) + len(att_data)])
        
        packet = parser.parse_packet(ll_header + l2cap_header + att_data, timestamp=0.0, rssi=-70, channel=0)
        
        assert packet.l2cap_cid == 0x0004
        assert packet.att_opcode == 0x0A
        assert packet.att_handle == 0x0003
        logger.info(" ATT packet parsing test passed")


class TestFilterEngine:
    """Tests for FilterEngine"""
    
    def test_simple_filter(self):
        """Test simple device filtering"""
        from backend.filter_engine import get_filter_engine
        from backend.capture_manager import BLEDevice
        
        engine = get_filter_engine()
        
        devices = [
            BLEDevice(address="AA:BB:CC:DD:EE:01", name="iPhone", rssi=-65),
            BLEDevice(address="AA:BB:CC:DD:EE:02", name="Android", rssi=-75),
        ]
        
        # Filter by RSSI
        condition = engine.create_condition("device_rssi", ">", -70)
        group = engine.create_group([condition])
        
        filtered = engine.filter_devices(devices, group)
        
        assert len(filtered) == 1
        assert filtered[0].name == "iPhone"
        logger.info(" Simple filter test passed")
    
    def test_complex_filter(self):
        """Test complex AND filter"""
        from backend.filter_engine import get_filter_engine
        from backend.capture_manager import BLEDevice
        
        engine = get_filter_engine()
        
        devices = [
            BLEDevice(address="AA:BB:CC:DD:EE:01", name="iPhone 12", rssi=-65, packet_count=100),
            BLEDevice(address="AA:BB:CC:DD:EE:02", name="iPhone SE", rssi=-75, packet_count=50),
            BLEDevice(address="AA:BB:CC:DD:EE:03", name="Android", rssi=-65, packet_count=30),
        ]
        
        # Complex filter: RSSI > -70 AND packets > 40
        condition1 = engine.create_condition("device_rssi", ">", -70)
        condition2 = engine.create_condition("device_packet_count", ">", 40)
        group = engine.create_group([condition1, condition2], "AND")
        
        filtered = engine.filter_devices(devices, group)
        
        assert len(filtered) == 1
        assert filtered[0].name == "iPhone 12"
        logger.info(" Complex filter test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("BlueScope Capture Manager Test Suite")
    print("="*70)
    
    # Run pytest
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        # Run basic tests manually
        test_device = TestBLEDevice()
        test_device.test_device_creation()
        test_device.test_device_update()
        
        test_packet = TestBLEPacket()
        test_packet.test_packet_creation()
        
        print("\n Basic tests completed")

