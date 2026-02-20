""" Signal Duplicator - Replay and duplicate captured Bluetooth signals Supports signal recording, replay, and live duplication """

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import json
import threading
import time
import random

logger = logging.getLogger(__name__)


@dataclass
class SignalRecord:
    """Recorded signal for duplication"""
    timestamp: datetime
    device_address: str
    signal_type: str
    rssi: int
    channel: int
    data: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)
    replay_count: int = 0


@dataclass
class DuplicationConfig:
    """Configuration for signal duplication"""
    enabled: bool = False
    replay_mode: str = "immediate"  # immediate, delayed, burst, random
    delay_ms: int = 0
    burst_count: int = 1
    random_interval_ms: tuple = (100, 1000)  # min, max
    max_replays: int = 0  # 0 = unlimited
    filter_device: Optional[str] = None  # None = all devices
    filter_signal_type: Optional[str] = None  # None = all types


class SignalDuplicator:
    """
    Duplicates and replays captured Bluetooth signals
    Features:
    - Record incoming signals
    - Replay signals with various modes
    - Live signal duplication
    - Signal modification and spoofing
    """
    
    def __init__(self, config: Optional[DuplicationConfig] = None):
        self.config = config or DuplicationConfig()
        self.is_recording = False
        self.is_replaying = False
        self.is_duplicating = False
        
        # Signal storage
        self.recorded_signals: deque = deque(maxlen=10000)
        self.signal_buffer: List[SignalRecord] = []
        
        # Statistics
        self.stats = {
            'recorded': 0,
            'replayed': 0,
            'duplicated': 0,
            'dropped': 0
        }
        
        # Callbacks
        self.on_signal_recorded: Optional[Callable[[SignalRecord], None]] = None
        self.on_signal_replayed: Optional[Callable[[SignalRecord], None]] = None
        self.on_signal_duplicated: Optional[Callable[[SignalRecord], None]] = None
        
        # Threads
        self._record_thread = None
        self._replay_thread = None
        self._duplicate_thread = None
        self._stop_event = threading.Event()
        
        logger.info("SignalDuplicator initialized")
    
    def start_recording(self):
        """Start recording signals"""
        if self.is_recording:
            logger.warning("Already recording")
            return
        
        self.is_recording = True
        self._stop_event.clear()
        logger.info("Signal recording started")
    
    def stop_recording(self):
        """Stop recording signals"""
        self.is_recording = False
        logger.info("Signal recording stopped")
    
    def start_replay(self, signals: Optional[List[SignalRecord]] = None):
        """Start replaying recorded signals"""
        if self.is_replaying:
            logger.warning("Already replaying")
            return
        
        self.is_replaying = True
        self._stop_event.clear()
        
        # Use provided signals or recorded ones
        replay_signals = signals or list(self.recorded_signals)
        
        # Start replay thread
        self._replay_thread = threading.Thread(
            target=self._replay_loop,
            args=(replay_signals,),
            daemon=True
        )
        self._replay_thread.start()
        
        logger.info(f"Signal replay started with {len(replay_signals)} signals")
    
    def stop_replay(self):
        """Stop replaying signals"""
        self.is_replaying = False
        self._stop_event.set()
        
        if self._replay_thread:
            self._replay_thread.join(timeout=2.0)
            self._replay_thread = None
        
        logger.info("Signal replay stopped")
    
    def start_duplication(self):
        """Start live signal duplication"""
        if self.is_duplicating:
            logger.warning("Already duplicating")
            return
        
        if not self.config.enabled:
            logger.warning("Duplication not enabled in config")
            return
        
        self.is_duplicating = True
        self._stop_event.clear()
        
        # Start duplication thread
        self._duplicate_thread = threading.Thread(
            target=self._duplicate_loop,
            daemon=True
        )
        self._duplicate_thread.start()
        
        logger.info("Live signal duplication started")
    
    def stop_duplication(self):
        """Stop live signal duplication"""
        self.is_duplicating = False
        self._stop_event.set()
        
        if self._duplicate_thread:
            self._duplicate_thread.join(timeout=2.0)
            self._duplicate_thread = None
        
        logger.info("Live signal duplication stopped")
    
    def record_signal(self, device_address: str, signal_type: str, 
                      rssi: int, channel: int, data: bytes,
                      metadata: Optional[Dict[str, Any]] = None):
        """Record a captured signal"""
        if not self.is_recording:
            return
        
        # Apply filters
        if self.config.filter_device and device_address != self.config.filter_device:
            return
        
        if self.config.filter_signal_type and signal_type != self.config.filter_signal_type:
            return
        
        record = SignalRecord(
            timestamp=datetime.now(),
            device_address=device_address,
            signal_type=signal_type,
            rssi=rssi,
            channel=channel,
            data=data,
            metadata=metadata or {}
        )
        
        self.recorded_signals.append(record)
        self.stats['recorded'] += 1
        
        if self.on_signal_recorded:
            self.on_signal_recorded(record)
        
        # If duplication is enabled, add to buffer
        if self.is_duplicating:
            self.signal_buffer.append(record)
        
        logger.debug(f"Recorded signal from {device_address}")
    
    def duplicate_signal(self, record: SignalRecord) -> List[SignalRecord]:
        """Duplicate a signal based on configuration"""
        if not self.config.enabled:
            return []
        
        duplicated = []
        
        # Check max replays
        if self.config.max_replays > 0 and record.replay_count >= self.config.max_replays:
            self.stats['dropped'] += 1
            return []
        
        # Create duplicates based on burst count
        for i in range(self.config.burst_count):
            dup = SignalRecord(
                timestamp=datetime.now(),
                device_address=record.device_address,
                signal_type=record.signal_type,
                rssi=record.rssi + random.randint(-5, 5),  # Slight RSSI variation
                channel=record.channel,
                data=record.data,
                metadata={
                    **record.metadata,
                    'duplicated': True,
                    'original_timestamp': record.timestamp.isoformat(),
                    'burst_index': i
                },
                replay_count=record.replay_count + 1
            )
            duplicated.append(dup)
            self.stats['duplicated'] += 1
        
        return duplicated
    
    def _replay_loop(self, signals: List[SignalRecord]):
        """Main replay loop"""
        logger.info(f"Replay loop started with {len(signals)} signals")
        
        for signal in signals:
            if self._stop_event.is_set():
                break
            
            if not self.is_replaying:
                break
            
            # Apply delay based on mode
            if self.config.replay_mode == "delayed":
                time.sleep(self.config.delay_ms / 1000.0)
            elif self.config.replay_mode == "random":
                delay = random.randint(
                    self.config.random_interval_ms[0],
                    self.config.random_interval_ms[1]
                ) / 1000.0
                time.sleep(delay)
            elif self.config.replay_mode == "burst":
                # No delay between burst packets
                pass
            
            # Emit replayed signal
            if self.on_signal_replayed:
                self.on_signal_replayed(signal)
            
            self.stats['replayed'] += 1
            
            logger.debug(f"Replayed signal from {signal.device_address}")
        
        self.is_replaying = False
        logger.info("Replay loop completed")
    
    def _duplicate_loop(self):
        """Main duplication loop for live signals"""
        logger.info("Duplication loop started")
        
        while self.is_duplicating and not self._stop_event.is_set():
            # Process signal buffer
            while self.signal_buffer:
                if self._stop_event.is_set():
                    break
                
                record = self.signal_buffer.pop(0)
                
                # Duplicate the signal
                duplicated = self.duplicate_signal(record)
                
                # Emit duplicated signals
                for dup in duplicated:
                    if self.on_signal_duplicated:
                        self.on_signal_duplicated(dup)
                    
                    # Small delay between burst packets
                    if self.config.replay_mode == "burst":
                        time.sleep(0.01)
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.001)
        
        self.is_duplicating = False
        logger.info("Duplication loop stopped")
    
    def get_recorded_signals(self, limit: int = 1000) -> List[SignalRecord]:
        """Get recorded signals"""
        return list(self.recorded_signals)[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get duplication statistics"""
        return {
            **self.stats,
            'buffer_size': len(self.signal_buffer),
            'recorded_signals': len(self.recorded_signals),
            'is_recording': self.is_recording,
            'is_replaying': self.is_replaying,
            'is_duplicating': self.is_duplicating
        }
    
    def clear_recorded(self):
        """Clear recorded signals"""
        self.recorded_signals.clear()
        self.stats['recorded'] = 0
        logger.info("Recorded signals cleared")
    
    def export_recorded(self, filepath: str):
        """Export recorded signals to JSON"""
        data = []
        for record in self.recorded_signals:
            data.append({
                'timestamp': record.timestamp.isoformat(),
                'device_address': record.device_address,
                'signal_type': record.signal_type,
                'rssi': record.rssi,
                'channel': record.channel,
                'data': record.data.hex() if record.data else '',
                'metadata': record.metadata
            })
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(data)} signals to {filepath}")
    
    def import_recorded(self, filepath: str):
        """Import recorded signals from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for item in data:
            record = SignalRecord(
                timestamp=datetime.fromisoformat(item['timestamp']),
                device_address=item['device_address'],
                signal_type=item['signal_type'],
                rssi=item['rssi'],
                channel=item['channel'],
                data=bytes.fromhex(item['data']) if item['data'] else b'',
                metadata=item.get('metadata', {})
            )
            self.recorded_signals.append(record)
        
        self.stats['recorded'] = len(self.recorded_signals)
        logger.info(f"Imported {len(data)} signals from {filepath}")


# Global instance
_duplicator: Optional[SignalDuplicator] = None


def get_signal_duplicator(config: Optional[DuplicationConfig] = None) -> SignalDuplicator:
    """Get or create global signal duplicator instance"""
    global _duplicator
    if _duplicator is None:
        _duplicator = SignalDuplicator(config)
    return _duplicator
