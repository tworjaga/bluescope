"""
Anomaly Engine - ML-Powered Anomaly Detection
Uses Isolation Forest, Autoencoders, and statistical methods for anomaly detection
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from dataclasses import dataclass, field
import json

# ML imports
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import torch
    import torch.nn as nn
    HAS_ML = True
except ImportError:
    HAS_ML = False
    torch = None
    nn = None
    logging.warning("ML libraries not available. Install scikit-learn and pytorch.")

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


@dataclass
class AnomalyStats:
    """Anomaly detection statistics"""
    total_anomalies: int = 0
    anomalies_by_type: Dict[str, int] = field(default_factory=dict)
    anomalies_by_severity: Dict[str, int] = field(default_factory=dict)
    false_positives: int = 0
    true_positives: int = 0
    detection_rate: float = 0.0


if HAS_ML:
    class Autoencoder(nn.Module):
        """Autoencoder for anomaly detection"""
        
        def __init__(self, input_dim: int, encoding_dim: int = 8):
            super(Autoencoder, self).__init__()
        
            # Encoder
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 32),
                nn.ReLU(),
                nn.Linear(32, 16),
                nn.ReLU(),
                nn.Linear(16, encoding_dim),
                nn.ReLU()
            )
            
            # Decoder
            self.decoder = nn.Sequential(
                nn.Linear(encoding_dim, 16),
                nn.ReLU(),
                nn.Linear(16, 32),
                nn.ReLU(),
                nn.Linear(32, input_dim),
                nn.Sigmoid()
            )
        
        def forward(self, x):
            encoded = self.encoder(x)
            decoded = self.decoder(encoded)
            return decoded
        
        def encode(self, x):
            return self.encoder(x)
else:
    class Autoencoder:
        """Dummy Autoencoder when ML libraries not available"""
        def __init__(self, *args, **kwargs):
            pass


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
        
        # ML models
        self.isolation_forest: Optional[IsolationForest] = None
        self.autoencoder: Optional[Autoencoder] = None
        self.scaler: Optional[StandardScaler] = None
        
        # Feature extraction
        self.feature_names = [
            'packet_rate',
            'avg_packet_size',
            'connection_duration',
            'rssi',
            'connection_interval',
            'service_count',
            'characteristic_count',
            'error_rate'
        ]
        
        # Anomaly storage
        self.anomalies: deque = deque(maxlen=10000)
        
        # Training data buffer
        self.training_buffer: deque = deque(maxlen=100000)
        
        # Statistics
        self.stats = AnomalyStats()
        
        # Thresholds
        self.isolation_threshold = -0.5
        self.autoencoder_threshold = 0.1
        self.statistical_threshold = 3.0  # Standard deviations
        
        # Running state
        self.is_running = False
        self.is_trained = False
        self.training_task = None
        self.detection_task = None
        
        # Initialize models if ML available
        if HAS_ML:
            self._initialize_models()
        
        logger.info("Anomaly Engine initialized")
    
    def _initialize_models(self):
        """Initialize ML models"""
        try:
            # Isolation Forest
            self.isolation_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            # Scaler
            self.scaler = StandardScaler()
            
            # Autoencoder
            if torch.cuda.is_available():
                self.device = torch.device('cuda')
                logger.info("Using GPU for autoencoder")
            else:
                self.device = torch.device('cpu')
            
            self.autoencoder = Autoencoder(
                input_dim=len(self.feature_names),
                encoding_dim=4
            ).to(self.device)
            
            logger.info("ML models initialized")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
    
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
    
    async def process_event(self, event: Dict[str, Any]):
        """Process event and detect anomalies"""
        try:
            # Extract features
            features = self._extract_features(event)
            
            # Add to training buffer
            self.training_buffer.append({
                'timestamp': datetime.now(),
                'device_id': event.get('device_id'),
                'features': features,
                'event': event
            })
            
            # Detect anomalies if trained
            if self.is_trained and HAS_ML:
                anomalies = await self._detect_anomalies(event, features)
                
                for anomaly in anomalies:
                    self.anomalies.append(anomaly)
                    self.stats.total_anomalies += 1
                    self.stats.anomalies_by_type[anomaly.anomaly_type] = \
                        self.stats.anomalies_by_type.get(anomaly.anomaly_type, 0) + 1
                    self.stats.anomalies_by_severity[anomaly.severity] = \
                        self.stats.anomalies_by_severity.get(anomaly.severity, 0) + 1
                    
                    logger.warning(f"Anomaly detected: {anomaly.description}")
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    def _extract_features(self, event: Dict[str, Any]) -> np.ndarray:
        """Extract features from event"""
        features = []
        
        # Extract each feature with defaults
        features.append(event.get('packet_rate', 0.0))
        features.append(event.get('avg_packet_size', 0.0))
        features.append(event.get('connection_duration', 0.0))
        features.append(event.get('rssi', -70.0))
        features.append(event.get('connection_interval', 0.0))
        features.append(len(event.get('services', [])))
        features.append(len(event.get('characteristics', [])))
        features.append(event.get('error_rate', 0.0))
        
        return np.array(features, dtype=np.float32)
    
    async def _detect_anomalies(
        self,
        event: Dict[str, Any],
        features: np.ndarray
    ) -> List[Anomaly]:
        """Detect anomalies using ensemble methods"""
        anomalies = []
        device_id = event.get('device_id', 'unknown')
        
        # Isolation Forest detection
        if self.isolation_forest is not None:
            iso_score = await self._isolation_forest_detect(features)
            if iso_score < self.isolation_threshold:
                anomalies.append(Anomaly(
                    anomaly_id=f"iso_{device_id}_{datetime.now().timestamp()}",
                    device_id=device_id,
                    anomaly_type='isolation_forest',
                    severity=self._calculate_severity(abs(iso_score)),
                    score=abs(iso_score),
                    description=f"Isolation Forest detected outlier (score: {iso_score:.3f})",
                    features=dict(zip(self.feature_names, features)),
                    timestamp=datetime.now()
                ))
        
        # Autoencoder detection
        if self.autoencoder is not None:
            ae_score = await self._autoencoder_detect(features)
            if ae_score > self.autoencoder_threshold:
                anomalies.append(Anomaly(
                    anomaly_id=f"ae_{device_id}_{datetime.now().timestamp()}",
                    device_id=device_id,
                    anomaly_type='autoencoder',
                    severity=self._calculate_severity(ae_score * 10),
                    score=ae_score,
                    description=f"Autoencoder detected anomaly (reconstruction error: {ae_score:.3f})",
                    features=dict(zip(self.feature_names, features)),
                    timestamp=datetime.now()
                ))
        
        # Statistical detection
        stat_anomalies = await self._statistical_detect(event, features)
        anomalies.extend(stat_anomalies)
        
        return anomalies
    
    async def _isolation_forest_detect(self, features: np.ndarray) -> float:
        """Detect anomalies using Isolation Forest"""
        try:
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Predict
            score = self.isolation_forest.score_samples(features_scaled)[0]
            
            return score
            
        except Exception as e:
            logger.error(f"Error in Isolation Forest detection: {e}")
            return 0.0
    
    async def _autoencoder_detect(self, features: np.ndarray) -> float:
        """Detect anomalies using Autoencoder"""
        try:
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Convert to tensor
            x = torch.FloatTensor(features_scaled).to(self.device)
            
            # Get reconstruction
            self.autoencoder.eval()
            with torch.no_grad():
                reconstruction = self.autoencoder(x)
            
            # Calculate reconstruction error
            error = torch.mean((x - reconstruction) ** 2).item()
            
            return error
            
        except Exception as e:
            logger.error(f"Error in Autoencoder detection: {e}")
            return 0.0
    
    async def _statistical_detect(
        self,
        event: Dict[str, Any],
        features: np.ndarray
    ) -> List[Anomaly]:
        """Detect anomalies using statistical methods"""
        anomalies = []
        device_id = event.get('device_id', 'unknown')
        
        # Get historical data for this device
        device_data = [
            d['features'] for d in self.training_buffer
            if d.get('device_id') == device_id
        ]
        
        if len(device_data) < 30:  # Need enough history
            return anomalies
        
        # Convert to array
        historical = np.array(device_data)
        
        # Check each feature
        for i, feature_name in enumerate(self.feature_names):
            mean = np.mean(historical[:, i])
            std = np.std(historical[:, i])
            
            if std > 0:
                z_score = abs((features[i] - mean) / std)
                
                if z_score > self.statistical_threshold:
                    anomalies.append(Anomaly(
                        anomaly_id=f"stat_{device_id}_{feature_name}_{datetime.now().timestamp()}",
                        device_id=device_id,
                        anomaly_type='statistical',
                        severity=self._calculate_severity(z_score / 3),
                        score=min(z_score / 5, 1.0),
                        description=f"Statistical anomaly in {feature_name}: {features[i]:.2f} (expected: {mean:.2f} ± {std:.2f})",
                        features={feature_name: features[i], 'z_score': z_score},
                        timestamp=datetime.now(),
                        metadata={'mean': mean, 'std': std}
                    ))
        
        return anomalies
    
    def _calculate_severity(self, score: float) -> str:
        """Calculate severity from anomaly score"""
        if score < 0.3:
            return 'low'
        elif score < 0.6:
            return 'medium'
        elif score < 0.8:
            return 'high'
        else:
            return 'critical'
    
    async def _training_loop(self):
        """Periodic model training"""
        while self.is_running:
            try:
                # Wait for enough data
                if len(self.training_buffer) >= 1000:
                    await self._train_models()
                
                # Train every hour
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in training loop: {e}")
                await asyncio.sleep(60)
    
    async def _train_models(self):
        """Train ML models"""
        if not HAS_ML:
            return
        
        try:
            logger.info("Training anomaly detection models...")
            
            # Prepare training data
            features_list = [d['features'] for d in self.training_buffer]
            X = np.array(features_list)
            
            # Fit scaler
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            
            # Train Isolation Forest
            self.isolation_forest.fit(X_scaled)
            
            # Train Autoencoder
            await self._train_autoencoder(X_scaled)
            
            self.is_trained = True
            logger.info("Model training complete")
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    async def _train_autoencoder(self, X: np.ndarray, epochs: int = 50):
        """Train autoencoder model"""
        try:
            # Convert to tensor
            X_tensor = torch.FloatTensor(X).to(self.device)
            
            # Setup training
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=0.001)
            
            # Training loop
            self.autoencoder.train()
            for epoch in range(epochs):
                # Forward pass
                outputs = self.autoencoder(X_tensor)
                loss = criterion(outputs, X_tensor)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Autoencoder epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
            
            logger.info("Autoencoder training complete")
            
        except Exception as e:
            logger.error(f"Error training autoencoder: {e}")
    
    async def _detection_loop(self):
        """Periodic anomaly detection tasks"""
        while self.is_running:
            try:
                # Update statistics
                await self._update_statistics()
                
                # Clean old anomalies
                await self._cleanup_old_anomalies()
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                await asyncio.sleep(5)
    
    async def _update_statistics(self):
        """Update detection statistics"""
        if len(self.anomalies) > 0:
            recent_anomalies = [
                a for a in self.anomalies
                if datetime.now() - a.timestamp <= timedelta(hours=1)
            ]
            
            if len(self.training_buffer) > 0:
                self.stats.detection_rate = len(recent_anomalies) / len(self.training_buffer)
    
    async def _cleanup_old_anomalies(self):
        """Remove old anomalies"""
        cutoff = datetime.now() - timedelta(days=7)
        
        # Anomalies are in a deque with maxlen, so they auto-cleanup
        # This is just for additional filtering if needed
        pass
    
    def get_anomalies(
        self,
        device_id: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Anomaly]:
        """Get detected anomalies"""
        anomalies = list(self.anomalies)
        
        if device_id:
            anomalies = [a for a in anomalies if a.device_id == device_id]
        
        if anomaly_type:
            anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]
        
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        
        # Sort by timestamp (newest first)
        anomalies.sort(key=lambda x: x.timestamp, reverse=True)
        
        return anomalies[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'total_anomalies': self.stats.total_anomalies,
            'anomalies_by_type': dict(self.stats.anomalies_by_type),
            'anomalies_by_severity': dict(self.stats.anomalies_by_severity),
            'detection_rate': self.stats.detection_rate,
            'is_trained': self.is_trained,
            'training_samples': len(self.training_buffer),
            'recent_anomalies': len([
                a for a in self.anomalies
                if datetime.now() - a.timestamp <= timedelta(hours=1)
            ])
        }
    
    def mark_false_positive(self, anomaly_id: str):
        """Mark anomaly as false positive"""
        for anomaly in self.anomalies:
            if anomaly.anomaly_id == anomaly_id:
                self.stats.false_positives += 1
                logger.info(f"Marked anomaly {anomaly_id} as false positive")
                break
    
    def mark_true_positive(self, anomaly_id: str):
        """Mark anomaly as true positive"""
        for anomaly in self.anomalies:
            if anomaly.anomaly_id == anomaly_id:
                self.stats.true_positives += 1
                logger.info(f"Marked anomaly {anomaly_id} as true positive")
                break


async def main():
    """Test anomaly engine"""
    logging.basicConfig(level=logging.INFO)
    
    engine = AnomalyEngine()
    await engine.start()
    
    # Simulate normal events
    for i in range(100):
        await engine.process_event({
            'device_id': 'device_001',
            'packet_rate': 10 + np.random.normal(0, 1),
            'avg_packet_size': 50 + np.random.normal(0, 5),
            'connection_duration': 30 + np.random.normal(0, 3),
            'rssi': -70 + np.random.normal(0, 5),
            'connection_interval': 100 + np.random.normal(0, 10),
            'services': ['battery', 'heart_rate'],
            'characteristics': ['char1', 'char2'],
            'error_rate': 0.01
        })
        await asyncio.sleep(0.01)
    
    # Wait for training
    await asyncio.sleep(2)
    
    # Simulate anomalous event
    await engine.process_event({
        'device_id': 'device_001',
        'packet_rate': 100,  # Anomalous
        'avg_packet_size': 200,  # Anomalous
        'connection_duration': 5,  # Anomalous
        'rssi': -90,  # Anomalous
        'connection_interval': 500,  # Anomalous
        'services': ['battery'],
        'characteristics': ['char1'],
        'error_rate': 0.5  # Anomalous
    })
    
    await asyncio.sleep(1)
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"\nEngine Statistics: {json.dumps(stats, indent=2)}")
    
    # Get anomalies
    anomalies = engine.get_anomalies(limit=10)
    print(f"\nDetected Anomalies: {len(anomalies)}")
    for anomaly in anomalies:
        print(f"  - {anomaly.description} (severity: {anomaly.severity}, score: {anomaly.score:.3f})")
    
    await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
