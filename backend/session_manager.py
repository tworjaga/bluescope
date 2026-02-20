"""
Session Manager - Save and load capture sessions
Provides session persistence with full state restoration
"""

import json
import pickle
import gzip
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import threading
import asyncio

from backend.capture_manager import BLEDevice, BLEPacket, CaptureManager
from backend.export_manager import ExportManager

logger = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    """Session metadata"""
    session_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    description: str = ""
    tags: List[str] = field(default_factory=list)
    capture_duration: float = 0.0  # seconds
    total_packets: int = 0
    total_devices: int = 0


@dataclass
class SessionData:
    """Complete session data"""
    metadata: SessionMetadata
    devices: List[Dict[str, Any]]
    packets: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    settings: Dict[str, Any]
    version: str = "1.0"


class SessionManager:
    """
    Manages capture session save/load functionality
    Supports multiple formats: JSON, Pickle, Compressed
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
        self._lock = threading.RLock()
        self.current_session: Optional[SessionMetadata] = None
        
        # Auto-save settings
        self.auto_save_enabled = False
        self.auto_save_interval = 300  # 5 minutes
        self._auto_save_task = None
        
        logger.info(f"SessionManager initialized (sessions dir: {self.sessions_dir})")
    
    def create_session(self, name: str, description: str = "", 
                       tags: Optional[List[str]] = None) -> SessionMetadata:
        """
        Create a new capture session
        
        Args:
            name: Session name
            description: Optional description
            tags: Optional list of tags
        
        Returns:
            SessionMetadata object
        """
        timestamp = datetime.now()
        session_id = f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}_{name.replace(' ', '_')}"
        
        metadata = SessionMetadata(
            session_id=session_id,
            name=name,
            created_at=timestamp,
            updated_at=timestamp,
            description=description,
            tags=tags or [],
            capture_duration=0.0,
            total_packets=0,
            total_devices=0
        )
        
        self.current_session = metadata
        
        logger.info(f"Created session: {name} ({session_id})")
        return metadata
    
    def save_session(self, capture_manager: CaptureManager, 
                     format: str = "compressed") -> str:
        """
        Save current capture session to disk
        
        Args:
            capture_manager: CaptureManager with current data
            format: 'json', 'pickle', or 'compressed'
        
        Returns:
            Path to saved session file
        """
        with self._lock:
            if self.current_session is None:
                # Create default session
                self.create_session("Untitled Session")
            
            # Update metadata
            self.current_session.updated_at = datetime.now()
            stats = capture_manager.get_statistics()
            self.current_session.total_packets = stats.get('total_packets', 0)
            self.current_session.total_devices = stats.get('total_devices', 0)
            self.current_session.capture_duration = stats.get('uptime', 0)
            
            # Prepare session data
            devices_data = []
            for device in capture_manager.get_devices():
                devices_data.append({
                    'address': device.address,
                    'name': device.name,
                    'rssi': device.rssi,
                    'manufacturer_data': {
                        str(k): v.hex() if isinstance(v, bytes) else v 
                        for k, v in device.manufacturer_data.items()
                    },
                    'service_uuids': device.service_uuids,
                    'tx_power': device.tx_power,
                    'first_seen': device.first_seen.isoformat(),
                    'last_seen': device.last_seen.isoformat(),
                    'packet_count': device.packet_count,
                    'is_connected': device.is_connected
                })
            
            packets_data = []
            for packet in capture_manager.get_packets(limit=10000):
                packets_data.append({
                    'timestamp': packet.timestamp.isoformat(),
                    'device_address': packet.device_address,
                    'packet_type': packet.packet_type,
                    'channel': packet.channel,
                    'rssi': packet.rssi,
                    'data': packet.data.hex(),
                    'metadata': packet.metadata
                })
            
            session_data = SessionData(
                metadata=self.current_session,
                devices=devices_data,
                packets=packets_data,
                statistics=stats,
                settings={
                    'backend': capture_manager.backend_type,
                    'config': capture_manager.config
                }
            )
            
            # Save to file
            filename = f"{self.current_session.session_id}"
            
            if format == "json":
                filepath = self.sessions_dir / f"{filename}.json"
                self._save_json(session_data, filepath)
            elif format == "pickle":
                filepath = self.sessions_dir / f"{filename}.pkl"
                self._save_pickle(session_data, filepath)
            else:  # compressed
                filepath = self.sessions_dir / f"{filename}.session.gz"
                self._save_compressed(session_data, filepath)
            
            logger.info(f"Session saved: {filepath} ({len(devices_data)} devices, {len(packets_data)} packets)")
            
            return str(filepath)
    
    def _save_json(self, session_data: SessionData, filepath: Path):
        """Save session as JSON"""
        data_dict = {
            'metadata': {
                'session_id': session_data.metadata.session_id,
                'name': session_data.metadata.name,
                'created_at': session_data.metadata.created_at.isoformat(),
                'updated_at': session_data.metadata.updated_at.isoformat(),
                'description': session_data.metadata.description,
                'tags': session_data.metadata.tags,
                'capture_duration': session_data.metadata.capture_duration,
                'total_packets': session_data.metadata.total_packets,
                'total_devices': session_data.metadata.total_devices
            },
            'devices': session_data.devices,
            'packets': session_data.packets,
            'statistics': session_data.statistics,
            'settings': session_data.settings,
            'version': session_data.version
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
    
    def _save_pickle(self, session_data: SessionData, filepath: Path):
        """Save session as Pickle"""
        with open(filepath, 'wb') as f:
            pickle.dump(session_data, f)
    
    def _save_compressed(self, session_data: SessionData, filepath: Path):
        """Save session as compressed Pickle"""
        with gzip.open(filepath, 'wb') as f:
            pickle.dump(session_data, f)
    
    def load_session(self, filepath: str) -> SessionData:
        """
        Load session from disk
        
        Args:
            filepath: Path to session file
        
        Returns:
            SessionData object
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Session file not found: {filepath}")
        
        # Determine format from extension
        if filepath.suffix == '.json':
            return self._load_json(filepath)
        elif filepath.suffix == '.pkl':
            return self._load_pickle(filepath)
        elif filepath.suffix == '.gz' or '.session' in filepath.name:
            return self._load_compressed(filepath)
        else:
            raise ValueError(f"Unknown session file format: {filepath}")
    
    def _load_json(self, filepath: Path) -> SessionData:
        """Load session from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
        
        metadata = SessionMetadata(
            session_id=data_dict['metadata']['session_id'],
            name=data_dict['metadata']['name'],
            created_at=datetime.fromisoformat(data_dict['metadata']['created_at']),
            updated_at=datetime.fromisoformat(data_dict['metadata']['updated_at']),
            description=data_dict['metadata'].get('description', ''),
            tags=data_dict['metadata'].get('tags', []),
            capture_duration=data_dict['metadata'].get('capture_duration', 0),
            total_packets=data_dict['metadata'].get('total_packets', 0),
            total_devices=data_dict['metadata'].get('total_devices', 0)
        )
        
        return SessionData(
            metadata=metadata,
            devices=data_dict['devices'],
            packets=data_dict['packets'],
            statistics=data_dict['statistics'],
            settings=data_dict.get('settings', {}),
            version=data_dict.get('version', '1.0')
        )
    
    def _load_pickle(self, filepath: Path) -> SessionData:
        """Load session from Pickle"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    def _load_compressed(self, filepath: Path) -> SessionData:
        """Load session from compressed Pickle"""
        with gzip.open(filepath, 'rb') as f:
            return pickle.load(f)
    
    def restore_session(self, session_data: SessionData, 
                       capture_manager: CaptureManager) -> bool:
        """
        Restore session data to capture manager
        
        Args:
            session_data: SessionData to restore
            capture_manager: CaptureManager to populate
        
        Returns:
            True if successful
        """
        try:
            # Restore devices
            for device_dict in session_data.devices:
                device = BLEDevice(
                    address=device_dict['address'],
                    name=device_dict['name'],
                    rssi=device_dict['rssi'],
                    manufacturer_data={
                        int(k): bytes.fromhex(v) if isinstance(v, str) else v
                        for k, v in device_dict.get('manufacturer_data', {}).items()
                    },
                    service_uuids=device_dict.get('service_uuids', []),
                    tx_power=device_dict.get('tx_power'),
                    first_seen=datetime.fromisoformat(device_dict['first_seen']),
                    last_seen=datetime.fromisoformat(device_dict['last_seen']),
                    packet_count=device_dict.get('packet_count', 0),
                    is_connected=device_dict.get('is_connected', False)
                )
                capture_manager.devices[device.address] = device
            
            # Restore packets
            for packet_dict in session_data.packets:
                packet = BLEPacket(
                    timestamp=datetime.fromisoformat(packet_dict['timestamp']),
                    device_address=packet_dict['device_address'],
                    packet_type=packet_dict['packet_type'],
                    channel=packet_dict['channel'],
                    rssi=packet_dict['rssi'],
                    data=bytes.fromhex(packet_dict['data']),
                    metadata=packet_dict.get('metadata', {})
                )
                capture_manager.packets.append(packet)
            
            # Update statistics
            capture_manager.stats.update(session_data.statistics)
            
            # Set current session
            self.current_session = session_data.metadata
            
            logger.info(f"Session restored: {session_data.metadata.name} "
                       f"({len(session_data.devices)} devices, "
                       f"{len(session_data.packets)} packets)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring session: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions
        
        Returns:
            List of session metadata dictionaries
        """
        sessions = []
        
        for filepath in self.sessions_dir.iterdir():
            if filepath.suffix in ['.json', '.pkl', '.gz'] or '.session' in filepath.name:
                try:
                    session_data = self.load_session(str(filepath))
                    sessions.append({
                        'filepath': str(filepath),
                        'session_id': session_data.metadata.session_id,
                        'name': session_data.metadata.name,
                        'created_at': session_data.metadata.created_at.isoformat(),
                        'updated_at': session_data.metadata.updated_at.isoformat(),
                        'description': session_data.metadata.description,
                        'tags': session_data.metadata.tags,
                        'total_devices': session_data.metadata.total_devices,
                        'total_packets': session_data.metadata.total_packets,
                        'capture_duration': session_data.metadata.capture_duration,
                        'size_bytes': filepath.stat().st_size
                    })
                except Exception as e:
                    logger.warning(f"Error loading session {filepath}: {e}")
        
        # Sort by updated_at (newest first)
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return sessions
    
    def delete_session(self, filepath: str) -> bool:
        """
        Delete a session file
        
        Args:
            filepath: Path to session file
        
        Returns:
            True if deleted successfully
        """
        try:
            Path(filepath).unlink()
            logger.info(f"Deleted session: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {filepath}: {e}")
            return False
    
    def rename_session(self, filepath: str, new_name: str) -> bool:
        """
        Rename a session
        
        Args:
            filepath: Path to session file
            new_name: New session name
        
        Returns:
            True if renamed successfully
        """
        try:
            session_data = self.load_session(filepath)
            session_data.metadata.name = new_name
            session_data.metadata.updated_at = datetime.now()
            
            # Save with new name
            self._save_compressed(session_data, Path(filepath))
            
            logger.info(f"Renamed session to: {new_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error renaming session: {e}")
            return False
    
    def export_session(self, filepath: str, export_format: str,
                       export_manager: ExportManager) -> Optional[str]:
        """
        Export session to different format
        
        Args:
            filepath: Path to session file
            export_format: 'csv', 'json', 'pcap'
            export_manager: ExportManager instance
        
        Returns:
            Path to exported file or None
        """
        try:
            session_data = self.load_session(filepath)
            
            if export_format == 'csv':
                # Export devices and packets as CSV
                devices_file = export_manager.export_devices_csv(session_data.devices)
                packets_file = export_manager.export_packets_csv([
                    {
                        'timestamp': p['timestamp'],
                        'device_address': p['device_address'],
                        'packet_type': p['packet_type'],
                        'channel': p['channel'],
                        'rssi': p['rssi'],
                        'length': len(p['data']) // 2,  # hex string to bytes
                        'data': p['data']
                    }
                    for p in session_data.packets
                ])
                return f"{devices_file}, {packets_file}"
            
            elif export_format == 'json':
                # Export as JSON
                export_data = {
                    'metadata': {
                        'session_id': session_data.metadata.session_id,
                        'name': session_data.metadata.name,
                        'created_at': session_data.metadata.created_at.isoformat(),
                        'description': session_data.metadata.description,
                        'tags': session_data.metadata.tags
                    },
                    'devices': session_data.devices,
                    'packets': session_data.packets,
                    'statistics': session_data.statistics
                }
                return export_manager.export_session_json(export_data)
            
            elif export_format == 'pcap':
                # Export packets as PCAP
                return export_manager.export_packets_pcap([
                    {
                        'timestamp': p['timestamp'],
                        'device_address': p['device_address'],
                        'packet_type': p['packet_type'],
                        'channel': p['channel'],
                        'rssi': p['rssi'],
                        'length': len(p['data']) // 2,
                        'data': p['data']
                    }
                    for p in session_data.packets
                ])
            
            else:
                logger.error(f"Unknown export format: {export_format}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return None
    
    async def enable_auto_save(self, capture_manager: CaptureManager,
                               interval_seconds: int = 300):
        """
        Enable automatic session saving
        
        Args:
            capture_manager: CaptureManager to auto-save
            interval_seconds: Auto-save interval
        """
        self.auto_save_enabled = True
        self.auto_save_interval = interval_seconds
        
        if self._auto_save_task is not None:
            return
        
        async def auto_save_loop():
            while self.auto_save_enabled:
                await asyncio.sleep(self.auto_save_interval)
                
                if self.auto_save_enabled and capture_manager.is_capturing:
                    try:
                        filepath = self.save_session(capture_manager, format="compressed")
                        logger.info(f"Auto-saved session: {filepath}")
                    except Exception as e:
                        logger.error(f"Auto-save failed: {e}")
        
        self._auto_save_task = asyncio.create_task(auto_save_loop())
        logger.info(f"Auto-save enabled (interval: {interval_seconds}s)")
    
    def disable_auto_save(self):
        """Disable automatic session saving"""
        self.auto_save_enabled = False
        
        if self._auto_save_task:
            self._auto_save_task.cancel()
            self._auto_save_task = None
        
        logger.info("Auto-save disabled")
    
    def get_session_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Get quick session info without loading full data
        
        Args:
            filepath: Path to session file
        
        Returns:
            Session metadata dictionary or None
        """
        try:
            session_data = self.load_session(filepath)
            return {
                'session_id': session_data.metadata.session_id,
                'name': session_data.metadata.name,
                'created_at': session_data.metadata.created_at.isoformat(),
                'updated_at': session_data.metadata.updated_at.isoformat(),
                'description': session_data.metadata.description,
                'tags': session_data.metadata.tags,
                'total_devices': session_data.metadata.total_devices,
                'total_packets': session_data.metadata.total_packets,
                'capture_duration': session_data.metadata.capture_duration
            }
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager(sessions_dir: str = "sessions") -> SessionManager:
    """Get or create global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(sessions_dir)
    return _session_manager


async def test_session_manager():
    """Test session manager functionality"""
    print("\n" + "="*60)
    print("Session Manager Test")
    print("="*60)
    
    from backend.capture_manager import CaptureManager
    
    # Create session manager
    session_mgr = get_session_manager("test_sessions")
    
    # Create capture manager with mock data
    capture_mgr = CaptureManager({'backend': 'mock'})
    
    # Simulate some capture
    print("\nSimulating capture...")
    await capture_mgr.start_capture()
    await asyncio.sleep(3)
    await capture_mgr.stop_capture()
    
    # Create and save session
    print("\nCreating session...")
    session_mgr.create_session(
        name="Test Capture Session",
        description="Testing session save/load functionality",
        tags=["test", "mock", "bluetooth"]
    )
    
    # Save session
    print("Saving session...")
    filepath = session_mgr.save_session(capture_mgr, format="compressed")
    print(f"   Saved to: {filepath}")
    
    # List sessions
    print("\nListing sessions...")
    sessions = session_mgr.list_sessions()
    print(f"  Found {len(sessions)} session(s)")
    for s in sessions[:3]:
        print(f"    - {s['name']} ({s['total_devices']} devices, {s['total_packets']} packets)")
    
    # Load and restore session
    print("\nLoading session...")
    session_data = session_mgr.load_session(filepath)
    print(f"   Loaded: {session_data.metadata.name}")
    print(f"     Devices: {len(session_data.devices)}")
    print(f"     Packets: {len(session_data.packets)}")
    
    # Create new capture manager and restore
    print("\nRestoring session to new capture manager...")
    new_capture_mgr = CaptureManager({'backend': 'mock'})
    success = session_mgr.restore_session(session_data, new_capture_mgr)
    print(f"  {'' if success else ''} Restore {'successful' if success else 'failed'}")
    
    if success:
        stats = new_capture_mgr.get_statistics()
        print(f"     Restored devices: {stats['total_devices']}")
        print(f"     Restored packets: {stats['total_packets']}")
    
    # Test auto-save
    print("\nTesting auto-save...")
    await session_mgr.enable_auto_save(capture_mgr, interval_seconds=2)
    await asyncio.sleep(5)
    session_mgr.disable_auto_save()
    print("   Auto-save test completed")
    
    # Cleanup
    print("\nCleaning up...")
    session_mgr.delete_session(filepath)
    import shutil
    if Path("test_sessions").exists():
        shutil.rmtree("test_sessions")
    print("   Cleanup completed")
    
    return True


if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_session_manager())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")
