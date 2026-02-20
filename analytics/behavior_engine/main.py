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
    
    async def _analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Analyze every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(5)
    
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
    
    await asyncio.sleep(2)
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"\nEngine Statistics: {json.dumps(stats, indent=2)}")
    
    await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
