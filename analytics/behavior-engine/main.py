"""
Behavior Engine - Pattern Analysis & Behavioral Modeling
Analyzes Bluetooth device behavior patterns and detects deviations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class DeviceBehavior:
    """Device behavior profile"""
    device_id: str
    mac_address: str
    first_seen: datetime
    last_seen: datetime
    
    # Connection patterns
    connection_count: int = 0
    avg_connection_duration: float = 0.0
    connection_intervals: List[float] = field(default_factory=list)
    
    # Communication patterns
    packet_count: int = 0
    avg_packet_size: float = 0.0
    packet_rate: float = 0.0
    
    # Service patterns
    services_used: set = field(default_factory=set)
    characteristics_accessed: set = field(default_factory=set)
    
    # Temporal patterns
    active_hours: List[int] = field(default_factory=list)
    active_days: List[int] = field(default_factory=list)
    
    # Behavioral scores
    regularity_score: float = 0.0
    predictability_score: float = 0.0
    anomaly_score: float = 0.0


@dataclass
class BehaviorPattern:
    """Detected behavior pattern"""
    pattern_id: str
    pattern_type: str  # periodic, burst, sequential, etc.
    devices: List[str]
    confidence: float
    first_detected: datetime
    last_detected: datetime
    occurrences: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorDeviation:
    """Detected behavioral deviation"""
    deviation_id: str
    device_id: str
    deviation_type: str
    severity: str  # low, medium, high, critical
    description: str
    expected_behavior: Dict[str, Any]
    observed_behavior: Dict[str, Any]
    timestamp: datetime
    confidence: float


class BehaviorEngine:
    """
    Behavior analysis engine for Bluetooth devices
    
    Features:
    - Pattern detection (periodic, burst, sequential)
    - Baseline profiling
    - Deviation detection
    - Behavioral clustering
    - Temporal analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Device profiles
        self.device_profiles: Dict[str, DeviceBehavior] = {}
        
        # Detected patterns
        self.patterns: Dict[str, BehaviorPattern] = {}
        
        # Recent deviations
        self.deviations: deque = deque(maxlen=10000)
        
        # Event buffers
        self.connection_events: deque = deque(maxlen=100000)
        self.packet_events: deque = deque(maxlen=100000)
        
        # Analysis parameters
        self.baseline_window = timedelta(hours=24)
        self.deviation_threshold = 2.5  # Standard deviations
        self.pattern_min_occurrences = 3
        
        # Statistics
        self.stats = {
            'devices_tracked': 0,
            'patterns_detected': 0,
            'deviations_detected': 0,
            'events_processed': 0
        }
        
        # Running state
        self.is_running = False
        self.analysis_task = None
        
        logger.info("Behavior Engine initialized")
    
    async def start(self):
        """Start behavior analysis engine"""
        if self.is_running:
            logger.warning("Behavior engine already running")
            return
        
        self.is_running = True
        self.analysis_task = asyncio.create_task(self._analysis_loop())
        logger.info("Behavior engine started")
    
    async def stop(self):
        """Stop behavior analysis engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Behavior engine stopped")
    
    async def process_connection_event(self, event: Dict[str, Any]):
        """Process connection event"""
        try:
            device_id = event.get('device_id')
            if not device_id:
                return
            
            # Add to event buffer
            self.connection_events.append({
                'timestamp': datetime.now(),
                'device_id': device_id,
                'event_type': event.get('event_type'),
                'duration': event.get('duration'),
                'metadata': event.get('metadata', {})
            })
            
            # Update device profile
            await self._update_device_profile(device_id, event)
            
            self.stats['events_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing connection event: {e}")
    
    async def process_packet_event(self, event: Dict[str, Any]):
        """Process packet event"""
        try:
            device_id = event.get('device_id')
            if not device_id:
                return
            
            # Add to event buffer
            self.packet_events.append({
                'timestamp': datetime.now(),
                'device_id': device_id,
                'packet_size': event.get('size'),
                'protocol': event.get('protocol'),
                'metadata': event.get('metadata', {})
            })
            
            # Update device profile
            await self._update_packet_stats(device_id, event)
            
            self.stats['events_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing packet event: {e}")
    
    async def _update_device_profile(self, device_id: str, event: Dict[str, Any]):
        """Update device behavior profile"""
        now = datetime.now()
        
        if device_id not in self.device_profiles:
            self.device_profiles[device_id] = DeviceBehavior(
                device_id=device_id,
                mac_address=event.get('mac_address', ''),
                first_seen=now,
                last_seen=now
            )
            self.stats['devices_tracked'] += 1
        
        profile = self.device_profiles[device_id]
        profile.last_seen = now
        
        # Update connection stats
        if event.get('event_type') == 'connection':
            profile.connection_count += 1
            
            if event.get('duration'):
                # Update average connection duration
                total_duration = profile.avg_connection_duration * (profile.connection_count - 1)
                profile.avg_connection_duration = (total_duration + event['duration']) / profile.connection_count
            
            # Track connection intervals
            if len(profile.connection_intervals) > 0:
                last_connection = profile.last_seen - timedelta(seconds=profile.connection_intervals[-1])
                interval = (now - last_connection).total_seconds()
                profile.connection_intervals.append(interval)
                
                # Keep only recent intervals
                if len(profile.connection_intervals) > 100:
                    profile.connection_intervals = profile.connection_intervals[-100:]
        
        # Update temporal patterns
        profile.active_hours.append(now.hour)
        profile.active_days.append(now.weekday())
        
        # Keep only recent temporal data
        if len(profile.active_hours) > 1000:
            profile.active_hours = profile.active_hours[-1000:]
            profile.active_days = profile.active_days[-1000:]
        
        # Update services and characteristics
        if 'services' in event:
            profile.services_used.update(event['services'])
        if 'characteristics' in event:
            profile.characteristics_accessed.update(event['characteristics'])
    
    async def _update_packet_stats(self, device_id: str, event: Dict[str, Any]):
        """Update packet statistics for device"""
        if device_id not in self.device_profiles:
            return
        
        profile = self.device_profiles[device_id]
        profile.packet_count += 1
        
        # Update average packet size
        if event.get('size'):
            total_size = profile.avg_packet_size * (profile.packet_count - 1)
            profile.avg_packet_size = (total_size + event['size']) / profile.packet_count
    
    async def _analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            try:
                # Run periodic analysis
                await self._detect_patterns()
                await self._detect_deviations()
                await self._update_behavioral_scores()
                
                # Sleep before next analysis
                await asyncio.sleep(60)  # Analyze every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(5)
    
    async def _detect_patterns(self):
        """Detect behavioral patterns"""
        try:
            # Detect periodic patterns
            await self._detect_periodic_patterns()
            
            # Detect burst patterns
            await self._detect_burst_patterns()
            
            # Detect sequential patterns
            await self._detect_sequential_patterns()
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
    
    async def _detect_periodic_patterns(self):
        """Detect periodic behavior patterns"""
        for device_id, profile in self.device_profiles.items():
            if len(profile.connection_intervals) < self.pattern_min_occurrences:
                continue
            
            # Calculate interval statistics
            intervals = np.array(profile.connection_intervals[-50:])
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            # Check for periodicity (low variance)
            if std_interval < mean_interval * 0.2:  # 20% variance threshold
                pattern_id = f"periodic_{device_id}_{int(mean_interval)}"
                
                if pattern_id not in self.patterns:
                    self.patterns[pattern_id] = BehaviorPattern(
                        pattern_id=pattern_id,
                        pattern_type='periodic',
                        devices=[device_id],
                        confidence=1.0 - (std_interval / mean_interval),
                        first_detected=datetime.now(),
                        last_detected=datetime.now(),
                        occurrences=1,
                        metadata={
                            'mean_interval': mean_interval,
                            'std_interval': std_interval
                        }
                    )
                    self.stats['patterns_detected'] += 1
                    logger.info(f"Detected periodic pattern for {device_id}: {mean_interval:.1f}s interval")
                else:
                    self.patterns[pattern_id].last_detected = datetime.now()
                    self.patterns[pattern_id].occurrences += 1
    
    async def _detect_burst_patterns(self):
        """Detect burst behavior patterns"""
        # Analyze packet events for burst activity
        now = datetime.now()
        window = timedelta(seconds=10)
        
        device_packets = defaultdict(list)
        
        # Group packets by device in recent window
        for event in self.packet_events:
            if now - event['timestamp'] <= window:
                device_packets[event['device_id']].append(event)
        
        # Detect bursts (high packet rate)
        for device_id, packets in device_packets.items():
            if len(packets) > 50:  # More than 50 packets in 10 seconds
                pattern_id = f"burst_{device_id}"
                
                if pattern_id not in self.patterns:
                    self.patterns[pattern_id] = BehaviorPattern(
                        pattern_id=pattern_id,
                        pattern_type='burst',
                        devices=[device_id],
                        confidence=min(len(packets) / 100, 1.0),
                        first_detected=now,
                        last_detected=now,
                        occurrences=1,
                        metadata={
                            'packet_count': len(packets),
                            'window_seconds': 10
                        }
                    )
                    self.stats['patterns_detected'] += 1
                    logger.info(f"Detected burst pattern for {device_id}: {len(packets)} packets")
    
    async def _detect_sequential_patterns(self):
        """Detect sequential behavior patterns"""
        # Analyze service access sequences
        for device_id, profile in self.device_profiles.items():
            if len(profile.services_used) >= 3:
                # Check for consistent service access order
                pattern_id = f"sequential_{device_id}"
                
                if pattern_id not in self.patterns:
                    self.patterns[pattern_id] = BehaviorPattern(
                        pattern_id=pattern_id,
                        pattern_type='sequential',
                        devices=[device_id],
                        confidence=0.8,
                        first_detected=datetime.now(),
                        last_detected=datetime.now(),
                        occurrences=1,
                        metadata={
                            'services': list(profile.services_used)
                        }
                    )
                    self.stats['patterns_detected'] += 1
    
    async def _detect_deviations(self):
        """Detect behavioral deviations"""
        try:
            for device_id, profile in self.device_profiles.items():
                # Check connection interval deviations
                await self._check_interval_deviation(device_id, profile)
                
                # Check packet rate deviations
                await self._check_packet_rate_deviation(device_id, profile)
                
                # Check temporal deviations
                await self._check_temporal_deviation(device_id, profile)
                
        except Exception as e:
            logger.error(f"Error detecting deviations: {e}")
    
    async def _check_interval_deviation(self, device_id: str, profile: DeviceBehavior):
        """Check for connection interval deviations"""
        if len(profile.connection_intervals) < 10:
            return
        
        intervals = np.array(profile.connection_intervals)
        mean = np.mean(intervals)
        std = np.std(intervals)
        
        if std > 0:
            # Check last interval
            last_interval = intervals[-1]
            z_score = abs((last_interval - mean) / std)
            
            if z_score > self.deviation_threshold:
                deviation = BehaviorDeviation(
                    deviation_id=f"interval_{device_id}_{datetime.now().timestamp()}",
                    device_id=device_id,
                    deviation_type='connection_interval',
                    severity='medium' if z_score < 4 else 'high',
                    description=f"Unusual connection interval: {last_interval:.1f}s (expected: {mean:.1f}s ± {std:.1f}s)",
                    expected_behavior={'mean': mean, 'std': std},
                    observed_behavior={'interval': last_interval, 'z_score': z_score},
                    timestamp=datetime.now(),
                    confidence=min(z_score / 5, 1.0)
                )
                
                self.deviations.append(deviation)
                self.stats['deviations_detected'] += 1
                logger.warning(f"Deviation detected for {device_id}: {deviation.description}")
    
    async def _check_packet_rate_deviation(self, device_id: str, profile: DeviceBehavior):
        """Check for packet rate deviations"""
        # Calculate recent packet rate
        now = datetime.now()
        window = timedelta(minutes=5)
        
        recent_packets = [
            e for e in self.packet_events
            if e['device_id'] == device_id and now - e['timestamp'] <= window
        ]
        
        if len(recent_packets) > 0:
            current_rate = len(recent_packets) / window.total_seconds()
            
            # Compare with historical rate
            if profile.packet_rate > 0:
                rate_change = abs(current_rate - profile.packet_rate) / profile.packet_rate
                
                if rate_change > 0.5:  # 50% change
                    deviation = BehaviorDeviation(
                        deviation_id=f"rate_{device_id}_{datetime.now().timestamp()}",
                        device_id=device_id,
                        deviation_type='packet_rate',
                        severity='medium',
                        description=f"Unusual packet rate: {current_rate:.2f} pkt/s (expected: {profile.packet_rate:.2f} pkt/s)",
                        expected_behavior={'rate': profile.packet_rate},
                        observed_behavior={'rate': current_rate, 'change': rate_change},
                        timestamp=datetime.now(),
                        confidence=min(rate_change, 1.0)
                    )
                    
                    self.deviations.append(deviation)
                    self.stats['deviations_detected'] += 1
            
            # Update profile rate
            profile.packet_rate = current_rate
    
    async def _check_temporal_deviation(self, device_id: str, profile: DeviceBehavior):
        """Check for temporal pattern deviations"""
        if len(profile.active_hours) < 50:
            return
        
        # Check if current hour is unusual
        current_hour = datetime.now().hour
        hour_frequency = profile.active_hours.count(current_hour) / len(profile.active_hours)
        
        if hour_frequency < 0.05:  # Less than 5% of activity in this hour
            deviation = BehaviorDeviation(
                deviation_id=f"temporal_{device_id}_{datetime.now().timestamp()}",
                device_id=device_id,
                deviation_type='temporal',
                severity='low',
                description=f"Unusual activity time: {current_hour}:00 (rarely active at this hour)",
                expected_behavior={'typical_hours': list(set(profile.active_hours))},
                observed_behavior={'current_hour': current_hour, 'frequency': hour_frequency},
                timestamp=datetime.now(),
                confidence=1.0 - hour_frequency
            )
            
            self.deviations.append(deviation)
            self.stats['deviations_detected'] += 1
    
    async def _update_behavioral_scores(self):
        """Update behavioral scores for all devices"""
        for device_id, profile in self.device_profiles.items():
            # Calculate regularity score (based on connection interval consistency)
            if len(profile.connection_intervals) > 5:
                intervals = np.array(profile.connection_intervals)
                cv = np.std(intervals) / np.mean(intervals) if np.mean(intervals) > 0 else 1.0
                profile.regularity_score = max(0, 1.0 - cv)
            
            # Calculate predictability score (based on temporal patterns)
            if len(profile.active_hours) > 20:
                hour_entropy = self._calculate_entropy(profile.active_hours)
                profile.predictability_score = max(0, 1.0 - hour_entropy / 4.5)  # Normalize
            
            # Calculate anomaly score (based on recent deviations)
            recent_deviations = [
                d for d in self.deviations
                if d.device_id == device_id and
                datetime.now() - d.timestamp <= timedelta(hours=1)
            ]
            profile.anomaly_score = min(len(recent_deviations) / 10, 1.0)
    
    def _calculate_entropy(self, data: List[int]) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        
        # Count frequencies
        freq = defaultdict(int)
        for item in data:
            freq[item] += 1
        
        # Calculate probabilities
        total = len(data)
        probs = [count / total for count in freq.values()]
        
        # Calculate entropy
        entropy = -sum(p * np.log2(p) for p in probs if p > 0)
        return entropy
    
    def get_device_profile(self, device_id: str) -> Optional[DeviceBehavior]:
        """Get device behavior profile"""
        return self.device_profiles.get(device_id)
    
    def get_patterns(self, pattern_type: Optional[str] = None) -> List[BehaviorPattern]:
        """Get detected patterns"""
        patterns = list(self.patterns.values())
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        return patterns
    
    def get_deviations(
        self,
        device_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[BehaviorDeviation]:
        """Get detected deviations"""
        deviations = list(self.deviations)
        
        if device_id:
            deviations = [d for d in deviations if d.device_id == device_id]
        
        if severity:
            deviations = [d for d in deviations if d.severity == severity]
        
        return deviations[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            **self.stats,
            'active_profiles': len(self.device_profiles),
            'active_patterns': len(self.patterns),
            'recent_deviations': len([
                d for d in self.deviations
                if datetime.now() - d.timestamp <= timedelta(hours=1)
            ])
        }


async def main():
    """Test behavior engine"""
    logging.basicConfig(level=logging.INFO)
    
    engine = BehaviorEngine()
    await engine.start()
    
    # Simulate some events
    for i in range(100):
        await engine.process_connection_event({
            'device_id': 'device_001',
            'mac_address': '00:11:22:33:44:55',
            'event_type': 'connection',
            'duration': 30 + np.random.normal(0, 5),
            'services': ['battery', 'heart_rate']
        })
        
        await asyncio.sleep(0.1)
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"\nEngine Statistics: {json.dumps(stats, indent=2)}")
    
    # Get device profile
    profile = engine.get_device_profile('device_001')
    if profile:
        print(f"\nDevice Profile:")
        print(f"  Connections: {profile.connection_count}")
        print(f"  Avg Duration: {profile.avg_connection_duration:.1f}s")
        print(f"  Regularity Score: {profile.regularity_score:.2f}")
    
    await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
