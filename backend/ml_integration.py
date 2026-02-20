"""
ML Integration Module - Integrates ML anomaly detection with live capture data
Provides real-time behavior analysis, device profiling, and anomaly alerts
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import threading
import numpy as np

from backend.capture_manager import BLEDevice, BLEPacket
from analytics.anomaly_engine.ml_detector import MLAnomalyDetector, AnomalyResult

logger = logging.getLogger(__name__)


@dataclass
class DeviceProfile:
    """Device behavior profile for baseline establishment"""
    device_address: str
    device_name: str
    first_seen: datetime
    last_seen: datetime
    
    # Packet statistics
    total_packets: int = 0
    packet_sizes: List[int] = field(default_factory=list)
    packet_timestamps: List[datetime] = field(default_factory=list)
    
    # RSSI statistics
    rssi_values: List[int] = field(default_factory=list)
    avg_rssi: float = 0.0
    rssi_variance: float = 0.0
    
    # Temporal patterns
    hourly_activity: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    daily_activity: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    # Channel usage
    channel_usage: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    # Behavior patterns
    is_periodic: bool = False
    is_burst_sender: bool = False
    regularity_score: float = 0.0
    
    # Baseline established
    baseline_established: bool = False
    baseline_samples: int = 0
    min_baseline_samples: int = 50


@dataclass
class BehaviorPattern:
    """Detected behavior pattern"""
    pattern_id: str
    pattern_type: str  # 'periodic', 'burst', 'sequential', 'random'
    device_address: str
    confidence: float
    description: str
    first_detected: datetime
    last_detected: datetime
    occurrences: int = 0


@dataclass
class AnomalyAlert:
    """Anomaly alert for GUI notification"""
    alert_id: str
    timestamp: datetime
    device_address: str
    device_name: str
    anomaly_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    score: float
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False


class MLIntegrationEngine:
    """
    Integrates ML anomaly detection with live Bluetooth capture data
    Provides real-time behavior analysis and anomaly alerting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # ML detector
        self.ml_detector = MLAnomalyDetector()
        
        # Device profiles
        self.device_profiles: Dict[str, DeviceProfile] = {}
        self.profile_lock = threading.RLock()
        
        # Behavior patterns
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}
        
        # Anomaly alerts
        self.anomaly_alerts: deque = deque(maxlen=1000)
        self.alert_counter = 0
        
        # Callbacks
        self.on_anomaly_detected: Optional[Callable[[AnomalyAlert], None]] = None
        self.on_pattern_detected: Optional[Callable[[BehaviorPattern], None]] = None
        self.on_profile_updated: Optional[Callable[[DeviceProfile], None]] = None
        
        # Training data buffer
        self.training_buffer: List[Dict] = []
        self.max_training_buffer = 1000
        
        # Baseline configuration
        self.baseline_window_minutes = self.config.get('baseline_window_minutes', 30)
        self.min_samples_for_baseline = self.config.get('min_samples_for_baseline', 50)
        
        # Running state
        self.is_running = False
        self.analysis_task = None
        
        logger.info("ML Integration Engine initialized")
    
    async def start(self):
        """Start ML integration engine"""
        if self.is_running:
            return
        
        self.is_running = True
        self.analysis_task = asyncio.create_task(self._analysis_loop())
        logger.info("ML Integration Engine started")
    
    async def stop(self):
        """Stop ML integration engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        
        logger.info("ML Integration Engine stopped")
    
    async def _analysis_loop(self):
        """Main analysis loop for periodic tasks"""
        while self.is_running:
            try:
                # Train ML model periodically
                if len(self.training_buffer) >= self.min_samples_for_baseline:
                    self._train_model()
                
                # Update device baselines
                self._update_baselines()
                
                # Detect behavior patterns
                self._detect_patterns()
                
                await asyncio.sleep(60)  # Run every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(5)
    
    def process_packet(self, packet: BLEPacket, device: BLEDevice):
        """
        Process a captured packet for ML analysis
        
        Args:
            packet: The BLE packet
            device: The device that sent the packet
        """
        try:
            # Update device profile
            profile = self._update_device_profile(packet, device)
            
            # Add to training buffer
            self._add_to_training_buffer(packet, device, profile)
            
            # Real-time anomaly detection
            if profile.baseline_established:
                self._detect_anomaly_realtime(packet, device, profile)
            
        except Exception as e:
            logger.error(f"Error processing packet for ML: {e}")
    
    def _update_device_profile(self, packet: BLEPacket, device: BLEDevice) -> DeviceProfile:
        """Update or create device profile"""
        with self.profile_lock:
            address = device.address
            
            if address not in self.device_profiles:
                profile = DeviceProfile(
                    device_address=address,
                    device_name=device.name,
                    first_seen=device.first_seen,
                    last_seen=device.last_seen,
                    min_baseline_samples=self.min_samples_for_baseline
                )
                self.device_profiles[address] = profile
                logger.info(f"Created profile for device: {device.name} ({address})")
            else:
                profile = self.device_profiles[address]
            
            # Update statistics
            profile.last_seen = device.last_seen
            profile.total_packets += 1
            profile.baseline_samples += 1
            
            # Packet size
            packet_size = len(packet.data)
            profile.packet_sizes.append(packet_size)
            if len(profile.packet_sizes) > 1000:
                profile.packet_sizes = profile.packet_sizes[-500:]
            
            # Timestamps
            profile.packet_timestamps.append(packet.timestamp)
            if len(profile.packet_timestamps) > 1000:
                profile.packet_timestamps = profile.packet_timestamps[-500:]
            
            # RSSI
            profile.rssi_values.append(packet.rssi)
            if len(profile.rssi_values) > 100:
                profile.rssi_values = profile.rssi_values[-50:]
            
            profile.avg_rssi = np.mean(profile.rssi_values) if profile.rssi_values else 0
            profile.rssi_variance = np.var(profile.rssi_values) if len(profile.rssi_values) > 1 else 0
            
            # Temporal patterns
            hour = packet.timestamp.hour
            day = packet.timestamp.weekday()
            profile.hourly_activity[hour] += 1
            profile.daily_activity[day] += 1
            
            # Channel usage
            profile.channel_usage[packet.channel] += 1
            
            # Check if baseline is established
            if not profile.baseline_established and profile.baseline_samples >= profile.min_baseline_samples:
                profile.baseline_established = True
                logger.info(f"Baseline established for {device.name} ({address}) - {profile.baseline_samples} samples")
                
                if self.on_profile_updated:
                    self.on_profile_updated(profile)
            
            return profile
    
    def _add_to_training_buffer(self, packet: BLEPacket, device: BLEDevice, profile: DeviceProfile):
        """Add sample to ML training buffer"""
        # Calculate features
        time_window = 60  # 1 minute window
        
        recent_packets = [
            ts for ts in profile.packet_timestamps
            if (packet.timestamp - ts).total_seconds() <= time_window
        ]
        
        feature_vector = {
            'packet_count': len(recent_packets),
            'time_window_seconds': time_window,
            'rssi_history': profile.rssi_values[-10:] if profile.rssi_values else [-70] * 10,
            'packet_sizes': profile.packet_sizes[-20:] if profile.packet_sizes else [20] * 20,
            'channels': list(profile.channel_usage.keys())[:10] or [37, 38, 39],
            'timestamps': [ts.timestamp() for ts in recent_packets[:10]] or list(range(10))
        }
        
        self.training_buffer.append(feature_vector)
        
        # Limit buffer size
        if len(self.training_buffer) > self.max_training_buffer:
            self.training_buffer = self.training_buffer[-self.max_training_buffer//2:]
    
    def _train_model(self):
        """Train ML model with collected data"""
        try:
            if len(self.training_buffer) < self.min_samples_for_baseline:
                return
            
            logger.info(f"Training ML model with {len(self.training_buffer)} samples...")
            
            success = self.ml_detector.train(self.training_buffer)
            
            if success:
                logger.info("ML model trained successfully")
                # Clear buffer after training
                self.training_buffer = []
            else:
                logger.warning("ML model training failed")
                
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def _detect_anomaly_realtime(self, packet: BLEPacket, device: BLEDevice, profile: DeviceProfile):
        """Perform real-time anomaly detection"""
        try:
            # Prepare feature vector
            time_window = 60
            
            recent_packets = [
                ts for ts in profile.packet_timestamps
                if (packet.timestamp - ts).total_seconds() <= time_window
            ]
            
            feature_vector = {
                'packet_count': len(recent_packets),
                'time_window_seconds': time_window,
                'rssi_history': profile.rssi_values[-10:] if profile.rssi_values else [-70] * 10,
                'packet_sizes': profile.packet_sizes[-20:] if profile.packet_sizes else [20] * 20,
                'channels': list(profile.channel_usage.keys())[:10] or [37, 38, 39],
                'timestamps': [ts.timestamp() for ts in recent_packets[:10]] or list(range(10))
            }
            
            # Detect anomaly
            result = self.ml_detector.detect_anomaly(feature_vector)
            
            if result and result.score > 0.7:  # High confidence threshold
                self._create_anomaly_alert(result, device, packet, profile)
                
        except Exception as e:
            logger.error(f"Error in real-time anomaly detection: {e}")
    
    def _create_anomaly_alert(self, result: AnomalyResult, device: BLEDevice, 
                              packet: BLEPacket, profile: DeviceProfile):
        """Create and dispatch anomaly alert"""
        self.alert_counter += 1
        
        alert = AnomalyAlert(
            alert_id=f"ALT-{self.alert_counter:06d}",
            timestamp=datetime.now(),
            device_address=device.address,
            device_name=device.name,
            anomaly_type=result.anomaly_type,
            severity=result.severity,
            score=result.score,
            description=result.description,
            details={
                'packet_type': packet.packet_type,
                'channel': packet.channel,
                'rssi': packet.rssi,
                'packet_size': len(packet.data),
                'profile_baseline_samples': profile.baseline_samples,
                'profile_avg_rssi': profile.avg_rssi
            }
        )
        
        self.anomaly_alerts.append(alert)
        
        logger.warning(f"Anomaly detected: {alert.description} (Score: {alert.score:.2f})")
        
        # Call callback
        if self.on_anomaly_detected:
            self.on_anomaly_detected(alert)
    
    def _update_baselines(self):
        """Update device baselines periodically"""
        with self.profile_lock:
            for address, profile in self.device_profiles.items():
                if not profile.baseline_established:
                    continue
                
                # Update behavior characteristics
                self._analyze_temporal_patterns(profile)
                self._analyze_packet_patterns(profile)
    
    def _analyze_temporal_patterns(self, profile: DeviceProfile):
        """Analyze temporal behavior patterns"""
        if len(profile.packet_timestamps) < 10:
            return
        
        # Check for periodicity
        intervals = []
        for i in range(1, min(len(profile.packet_timestamps), 100)):
            interval = (profile.packet_timestamps[-i] - profile.packet_timestamps[-i-1]).total_seconds()
            intervals.append(interval)
        
        if intervals:
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            # Low variance indicates periodic behavior
            if std_interval < mean_interval * 0.2 and mean_interval > 0:
                profile.is_periodic = True
                profile.regularity_score = min(1.0, 1.0 - (std_interval / mean_interval))
            else:
                profile.is_periodic = False
                profile.regularity_score = 0.0
    
    def _analyze_packet_patterns(self, profile: DeviceProfile):
        """Analyze packet size and timing patterns"""
        if len(profile.packet_sizes) < 20:
            return
        
        # Check for burst behavior (many packets in short time)
        recent_timestamps = profile.packet_timestamps[-20:]
        if len(recent_timestamps) >= 10:
            time_span = (recent_timestamps[-1] - recent_timestamps[0]).total_seconds()
            packet_rate = len(recent_timestamps) / max(time_span, 1)
            
            # High packet rate indicates burst behavior
            profile.is_burst_sender = packet_rate > 10  # More than 10 packets per second
    
    def _detect_patterns(self):
        """Detect behavior patterns across all devices"""
        with self.profile_lock:
            for address, profile in self.device_profiles.items():
                if not profile.baseline_established:
                    continue
                
                # Detect pattern type
                pattern_type = self._classify_pattern(profile)
                
                if pattern_type != 'unknown':
                    pattern_id = f"PAT-{address[:8]}-{pattern_type}"
                    
                    if pattern_id not in self.behavior_patterns:
                        pattern = BehaviorPattern(
                            pattern_id=pattern_id,
                            pattern_type=pattern_type,
                            device_address=address,
                            confidence=profile.regularity_score,
                            description=f"{pattern_type.capitalize()} behavior detected",
                            first_detected=datetime.now(),
                            last_detected=datetime.now(),
                            occurrences=1
                        )
                        self.behavior_patterns[pattern_id] = pattern
                        
                        logger.info(f"New pattern detected: {pattern.description} for {profile.device_name}")
                        
                        if self.on_pattern_detected:
                            self.on_pattern_detected(pattern)
                    else:
                        # Update existing pattern
                        pattern = self.behavior_patterns[pattern_id]
                        pattern.last_detected = datetime.now()
                        pattern.occurrences += 1
    
    def _classify_pattern(self, profile: DeviceProfile) -> str:
        """Classify device behavior pattern"""
        if profile.is_periodic and profile.regularity_score > 0.8:
            return 'periodic'
        elif profile.is_burst_sender:
            return 'burst'
        elif profile.regularity_score > 0.5:
            return 'sequential'
        else:
            return 'random'
    
    def get_device_profile(self, address: str) -> Optional[DeviceProfile]:
        """Get profile for a specific device"""
        with self.profile_lock:
            return self.device_profiles.get(address)
    
    def get_all_profiles(self) -> List[DeviceProfile]:
        """Get all device profiles"""
        with self.profile_lock:
            return list(self.device_profiles.values())
    
    def get_recent_alerts(self, limit: int = 100, 
                         severity_filter: Optional[str] = None) -> List[AnomalyAlert]:
        """Get recent anomaly alerts"""
        alerts = list(self.anomaly_alerts)
        
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]
        
        return alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an anomaly alert"""
        for alert in self.anomaly_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ML integration statistics"""
        with self.profile_lock:
            total_profiles = len(self.device_profiles)
            established_baselines = sum(1 for p in self.device_profiles.values() if p.baseline_established)
            
            return {
                'total_profiles': total_profiles,
                'established_baselines': established_baselines,
                'pending_baselines': total_profiles - established_baselines,
                'total_alerts': len(self.anomaly_alerts),
                'unacknowledged_alerts': sum(1 for a in self.anomaly_alerts if not a.acknowledged),
                'detected_patterns': len(self.behavior_patterns),
                'ml_model_trained': self.ml_detector.is_trained if hasattr(self.ml_detector, 'is_trained') else False,
                'training_samples': len(self.training_buffer)
            }


# Global ML integration instance
_ml_integration: Optional[MLIntegrationEngine] = None


def get_ml_integration(config: Optional[Dict[str, Any]] = None) -> MLIntegrationEngine:
    """Get or create global ML integration instance"""
    global _ml_integration
    if _ml_integration is None:
        _ml_integration = MLIntegrationEngine(config)
    return _ml_integration


async def test_ml_integration():
    """Test ML integration with mock data"""
    print("\n" + "="*60)
    print("ML Integration Test")
    print("="*60)
    
    from backend.capture_manager import BLEDevice, BLEPacket
    
    ml_engine = get_ml_integration({
        'baseline_window_minutes': 5,
        'min_samples_for_baseline': 20
    })
    
    # Set up callbacks
    def on_anomaly(alert):
        print(f"   ANOMALY: {alert.description} (Severity: {alert.severity})")
    
    def on_pattern(pattern):
        print(f"   PATTERN: {pattern.description} (Confidence: {pattern.confidence:.2f})")
    
    def on_profile(profile):
        print(f"   BASELINE: Established for {profile.device_name}")
    
    ml_engine.on_anomaly_detected = on_anomaly
    ml_engine.on_pattern_detected = on_pattern
    ml_engine.on_profile_updated = on_profile
    
    # Start engine
    await ml_engine.start()
    
    # Simulate packets
    print("\nSimulating device traffic...")
    
    mock_device = BLEDevice(
        address="AA:BB:CC:DD:EE:01",
        name="Test Device",
        rssi=-65
    )
    
    # Normal traffic (50 packets)
    print("  Sending normal traffic (50 packets)...")
    for i in range(50):
        packet = BLEPacket(
            timestamp=datetime.now(),
            device_address=mock_device.address,
            packet_type="ADV_IND",
            channel=37 + (i % 3),
            rssi=-65 + (i % 5),
            data=bytes([0x02, 0x01, 0x06] + [0x00] * 20)
        )
        ml_engine.process_packet(packet, mock_device)
        await asyncio.sleep(0.01)
    
    # Wait for baseline establishment
    print("  Waiting for baseline establishment...")
    await asyncio.sleep(2)
    
    # Anomalous traffic (high packet rate)
    print("  Sending anomalous traffic (burst)...")
    for i in range(20):
        packet = BLEPacket(
            timestamp=datetime.now(),
            device_address=mock_device.address,
            packet_type="ADV_IND",
            channel=99,  # Invalid channel
            rssi=-30,  # Unusual RSSI
            data=bytes([0xFF] * 200)  # Large packet
        )
        ml_engine.process_packet(packet, mock_device)
    
    # Wait for detection
    await asyncio.sleep(2)
    
    # Print statistics
    stats = ml_engine.get_statistics()
    print(f"\nML Integration Statistics:")
    print(f"  Total profiles: {stats['total_profiles']}")
    print(f"  Established baselines: {stats['established_baselines']}")
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Unacknowledged alerts: {stats['unacknowledged_alerts']}")
    print(f"  Detected patterns: {stats['detected_patterns']}")
    print(f"  ML model trained: {stats['ml_model_trained']}")
    
    # Stop engine
    await ml_engine.stop()
    
    return stats['total_alerts'] > 0 or stats['established_baselines'] > 0


if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_ml_integration())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")
