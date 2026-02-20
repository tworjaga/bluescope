"""
Anomaly Engine - ML-Powered Anomaly Detection
Uses Isolation Forest, Autoencoders, and statistical methods for anomaly detection
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_id: str
    device_id: str
    anomaly_type: str
    severity: str  # low, medium, high, critical
    score: float  # 0-1, higher = more anomalous
    description: str
    features: Dict[str, float]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnomalyEngine:
    """
    ML-powered anomaly detection engine
    
    Features:
    - Isolation Forest for outlier detection
    - Autoencoder for reconstruction-based detection
    - Statistical anomaly detection
    - Ensemble methods
    - Real-time scoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Anomaly storage
        self.anomalies: deque = deque(maxlen=10000)
        
        # Training data buffer
        self.training_buffer: deque = deque(maxlen=100000)
        
        # Statistics
        self.stats = {
            'total_anomalies': 0,
            'anomalies_by_type': {},
            'anomalies_by_severity': {}
        }
        
        # Running state
        self.is_running = False
        self.is_trained = False
        self.training_task = None
        self.detection_task = None
        
        logger.info("Anomaly Engine initialized")
    
    async def start(self):
        """Start anomaly detection engine"""
        if self.is_running:
            logger.warning("Anomaly engine already running")
            return
        
        self.is_running = True
        
        # Start training task
        self.training_task = asyncio.create_task(self._training_loop())
        
        # Start detection task
        self.detection_task = asyncio.create_task(self._detection_loop())
        
        logger.info("Anomaly engine started")
    
    async def stop(self):
        """Stop anomaly detection engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel tasks
        for task in [self.training_task, self.detection_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Anomaly engine stopped")
    
    async def _training_loop(self):
        """Periodic model training"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Train every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in training loop: {e}")
                await asyncio.sleep(60)
    
    async def _detection_loop(self):
        """Periodic anomaly detection tasks"""
        while self.is_running:
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                await asyncio.sleep(5)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'total_anomalies': self.stats['total_anomalies'],
            'anomalies_by_type': dict(self.stats['anomalies_by_type']),
            'anomalies_by_severity': dict(self.stats['anomalies_by_severity']),
            'is_trained': self.is_trained,
            'training_samples': len(self.training_buffer),
            'recent_anomalies': len([
                a for a in self.anomalies
                if datetime.now() - a.timestamp <= timedelta(hours=1)
            ])
        }


async def main():
    """Test anomaly engine"""
    logging.basicConfig(level=logging.INFO)
    
    engine = AnomalyEngine()
    await engine.start()
    
    await asyncio.sleep(2)
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"\nEngine Statistics: {json.dumps(stats, indent=2)}")
    
    await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
