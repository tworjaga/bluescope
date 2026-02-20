"""
Export Manager - Handles data export to various formats
Supports: CSV, JSON, PCAP
"""

import csv
import json
import logging
import struct
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import os

logger = logging.getLogger(__name__)


class ExportManager:
    """
    Manages export of captured data to various formats
    """
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
        logger.info(f"ExportManager initialized with directory: {self.export_dir}")
    
    def export_devices_csv(self, devices: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export device list to CSV
        
        Args:
            devices: List of device dictionaries
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not devices:
                    logger.warning("No devices to export")
                    return str(filepath)
                
                # Get fieldnames from first device
                fieldnames = list(devices[0].keys())
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(devices)
            
            logger.info(f"Exported {len(devices)} devices to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting devices to CSV: {e}")
            raise
    
    def export_packets_csv(self, packets: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export packets to CSV
        
        Args:
            packets: List of packet dictionaries
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"packets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not packets:
                    logger.warning("No packets to export")
                    return str(filepath)
                
                # Get fieldnames from first packet
                fieldnames = list(packets[0].keys())
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(packets)
            
            logger.info(f"Exported {len(packets)} packets to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting packets to CSV: {e}")
            raise
    
    def export_session_json(self, session_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Export complete session to JSON
        
        Args:
            session_data: Dictionary containing session data (devices, packets, anomalies, etc.)
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.export_dir / filename
        
        try:
            # Add metadata
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'version': '1.0',
                    'format': 'bluescope_session'
                },
                'data': session_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported session to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting session to JSON: {e}")
            raise
    
    def export_packets_pcap(self, packets: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export packets to PCAP format (Wireshark compatible)
        
        Args:
            packets: List of packet dictionaries
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'wb') as f:
                # Write PCAP global header
                # Magic number (little endian)
                f.write(struct.pack('<I', 0xa1b2c3d4))
                # Version major
                f.write(struct.pack('<H', 2))
                # Version minor
                f.write(struct.pack('<H', 4))
                # Timezone (GMT)
                f.write(struct.pack('<i', 0))
                # Sigfigs
                f.write(struct.pack('<I', 0))
                # Snaplen
                f.write(struct.pack('<I', 65535))
                # Network (LINKTYPE_BLUETOOTH_LE_LL = 251)
                f.write(struct.pack('<I', 251))
                
                # Write packet records
                for packet in packets:
                    # Convert timestamp to seconds and microseconds
                    timestamp = packet.get('timestamp', datetime.now())
                    if isinstance(timestamp, datetime):
                        ts_sec = int(timestamp.timestamp())
                        ts_usec = int((timestamp.timestamp() - ts_sec) * 1000000)
                    else:
                        ts_sec = int(timestamp)
                        ts_usec = 0
                    
                    # Get packet data
                    data = packet.get('data', b'')
                    if isinstance(data, str):
                        # Try to convert from hex string
                        try:
                            data = bytes.fromhex(data.replace(':', ''))
                        except:
                            data = data.encode('utf-8', errors='ignore')
                    
                    # Packet header
                    f.write(struct.pack('<I', ts_sec))      # Timestamp seconds
                    f.write(struct.pack('<I', ts_usec))     # Timestamp microseconds
                    f.write(struct.pack('<I', len(data)))   # Captured length
                    f.write(struct.pack('<I', len(data)))   # Original length
                    
                    # Packet data
                    f.write(data)
            
            logger.info(f"Exported {len(packets)} packets to PCAP: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting packets to PCAP: {e}")
            raise
    
    def export_anomalies_csv(self, anomalies: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export anomalies to CSV
        
        Args:
            anomalies: List of anomaly dictionaries
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"anomalies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not anomalies:
                    logger.warning("No anomalies to export")
                    return str(filepath)
                
                # Get fieldnames from first anomaly
                fieldnames = list(anomalies[0].keys())
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(anomalies)
            
            logger.info(f"Exported {len(anomalies)} anomalies to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting anomalies to CSV: {e}")
            raise
    
    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get list of exported files"""
        exports = []
        
        try:
            for filepath in self.export_dir.iterdir():
                if filepath.is_file():
                    stat = filepath.stat()
                    exports.append({
                        'filename': filepath.name,
                        'path': str(filepath),
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'format': filepath.suffix.lower()
                    })
            
            # Sort by creation time (newest first)
            exports.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting export history: {e}")
        
        return exports
    
    def delete_export(self, filename: str) -> bool:
        """Delete an exported file"""
        try:
            filepath = self.export_dir / filename
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted export: {filename}")
                return True
            else:
                logger.warning(f"Export file not found: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting export: {e}")
            return False
    
    def clear_all_exports(self) -> int:
        """Delete all exported files"""
        count = 0
        
        try:
            for filepath in self.export_dir.iterdir():
                if filepath.is_file():
                    filepath.unlink()
                    count += 1
            
            logger.info(f"Cleared {count} exported files")
            
        except Exception as e:
            logger.error(f"Error clearing exports: {e}")
        
        return count


# Global export manager instance
_export_manager: Optional[ExportManager] = None


def get_export_manager(export_dir: str = "exports") -> ExportManager:
    """Get or create global export manager instance"""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager(export_dir)
    return _export_manager
