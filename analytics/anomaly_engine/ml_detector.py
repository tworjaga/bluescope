"""
ML-Powered Anomaly Detection
Implements Isolation Forest and Autoencoder-based anomaly detection
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import deque
import pickle
import os

logger = logging.getLogger(__name__)

# Try to import scikit-learn
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available. ML detection will be limited.")
    SKLEARN_AVAILABLE = False

# Try to import PyTorch for autoencoder
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available. Autoencoder detection disabled.")
    TORCH_AVAILABLE = False


@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    score: float  # 0-1, higher = more anomalous
    anomaly_type: str
    severity: str  # low, medium, high, critical
    features: Dict[str, float]
    description: str
    timestamp: datetime


class Autoencoder(nn.Module):
    """Simple autoencoder for anomaly detection"""
    
    def __init__(self, input_dim: int, encoding_dim: int = 8):
        super(Autoencoder, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, encoding_dim),
            nn.ReLU()
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class MLAnomalyDetector:
    """
    ML-powered anomaly detector using Isolation Forest and Autoencoder
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Isolation Forest parameters
        self.contamination = self.config.get('contamination', 0.1)
        self.n_estimators = self.config.get('n_estimators', 100)
        self.isolation_forest = None
        self.scaler = None
        
        # Autoencoder parameters
        self.autoencoder = None
        self.autoencoder_threshold = self.config.get('autoencoder_threshold', 0.1)
        
        # Training data buffer
        self.training_buffer = deque(maxlen=10000)
        self.is_trained = False
        
        # Feature names
        self.feature_names = [
            'packet_rate', 'rssi_mean', 'rssi_std', 'packet_size_mean',
            'packet_size_std', 'channel_variance', 'time_variance', 'burstiness'
        ]
        
        # Model paths
        self.model_dir = self.config.get('model_dir', 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        self._load_models()
        
        logger.info("ML Anomaly Detector initialized")
    
    def _load_models(self):
        """Load pre-trained models if available"""
        if not SKLEARN_AVAILABLE:
            return
        
        try:
            # Try to load Isolation Forest
            if_path = os.path.join(self.model_dir, 'isolation_forest.pkl')
            if os.path.exists(if_path):
                with open(if_path, 'rb') as f:
                    self.isolation_forest = pickle.load(f)
                logger.info("Loaded Isolation Forest model")
            
            # Try to load scaler
            scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("Loaded scaler")
            
            if self.isolation_forest and self.scaler:
                self.is_trained = True
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def _save_models(self):
        """Save trained models"""
        if not SKLEARN_AVAILABLE:
            return
        
        try:
            if self.isolation_forest:
                if_path = os.path.join(self.model_dir, 'isolation_forest.pkl')
                with open(if_path, 'wb') as f:
                    pickle.dump(self.isolation_forest, f)
                logger.info("Saved Isolation Forest model")
            
            if self.scaler:
                scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scaler, f)
                logger.info("Saved scaler")
                
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def extract_features(self, device_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from device data for anomaly detection
        
        Features:
        - packet_rate: packets per second
        - rssi_mean: average RSSI
        - rssi_std: RSSI standard deviation
        - packet_size_mean: average packet size
        - packet_size_std: packet size standard deviation
        - channel_variance: variance in channels used
        - time_variance: variance in packet timing
        - burstiness: measure of burstiness in traffic
        """
        features = np.zeros(len(self.feature_names))
        
        # Packet rate
        packet_count = device_data.get('packet_count', 0)
        time_window = device_data.get('time_window_seconds', 60)
        features[0] = packet_count / max(time_window, 1)
        
        # RSSI statistics
        rssi_values = device_data.get('rssi_history', [-70])
        features[1] = np.mean(rssi_values)
        features[2] = np.std(rssi_values) if len(rssi_values) > 1 else 0
        
        # Packet size statistics
        packet_sizes = device_data.get('packet_sizes', [20])
        features[3] = np.mean(packet_sizes)
        features[4] = np.std(packet_sizes) if len(packet_sizes) > 1 else 0
        
        # Channel variance
        channels = device_data.get('channels', [37])
        features[5] = np.var(channels) if len(channels) > 1 else 0
        
        # Time variance (inter-packet arrival times)
        timestamps = device_data.get('timestamps', [])
        if len(timestamps) > 1:
            intervals = np.diff(timestamps)
            features[6] = np.var(intervals)
            features[7] = np.std(intervals) / (np.mean(intervals) + 0.001)  # Coefficient of variation
        else:
            features[6] = 0
            features[7] = 0
        
        return features
    
    def train(self, device_data_list: List[Dict[str, Any]]):
        """
        Train ML models on device data
        
        Args:
            device_data_list: List of device data dictionaries
        """
        if not SKLEARN_AVAILABLE or len(device_data_list) < 10:
            logger.warning("Not enough data or sklearn not available for training")
            return False
        
        try:
            # Extract features from all devices
            features_list = []
            for device_data in device_data_list:
                features = self.extract_features(device_data)
                features_list.append(features)
            
            X = np.array(features_list)
            
            # Fit scaler
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.isolation_forest = IsolationForest(
                n_estimators=self.n_estimators,
                contamination=self.contamination,
                random_state=42,
                n_jobs=-1
            )
            self.isolation_forest.fit(X_scaled)
            
            # Train Autoencoder if PyTorch available
            if TORCH_AVAILABLE:
                self._train_autoencoder(X_scaled)
            
            self.is_trained = True
            self._save_models()
            
            logger.info(f"Trained ML models on {len(device_data_list)} devices")
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def _train_autoencoder(self, X: np.ndarray):
        """Train autoencoder for anomaly detection"""
        if not TORCH_AVAILABLE:
            return
        
        try:
            input_dim = X.shape[1]
            self.autoencoder = Autoencoder(input_dim)
            
            # Convert to tensor
            X_tensor = torch.FloatTensor(X)
            
            # Training parameters
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=0.001)
            epochs = 50
            batch_size = 32
            
            # Training loop
            self.autoencoder.train()
            for epoch in range(epochs):
                total_loss = 0
                for i in range(0, len(X_tensor), batch_size):
                    batch = X_tensor[i:i+batch_size]
                    
                    # Forward pass
                    output = self.autoencoder(batch)
                    loss = criterion(output, batch)
                    
                    # Backward pass
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                if epoch % 10 == 0:
                    logger.debug(f"Autoencoder Epoch {epoch}, Loss: {total_loss:.4f}")
            
            logger.info("Autoencoder training completed")
            
        except Exception as e:
            logger.error(f"Error training autoencoder: {e}")
    
    def detect_anomaly(self, device_data: Dict[str, Any]) -> Optional[AnomalyResult]:
        """
        Detect anomaly in device data
        
        Returns:
            AnomalyResult if anomaly detected, None otherwise
        """
        if not SKLEARN_AVAILABLE or not self.is_trained:
            return None
        
        try:
            # Extract features
            features = self.extract_features(device_data)
            X = features.reshape(1, -1)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Isolation Forest prediction
            if_score = self.isolation_forest.decision_function(X_scaled)[0]
            if_prediction = self.isolation_forest.predict(X_scaled)[0]
            
            # Convert to anomaly score (0-1, higher = more anomalous)
            # Isolation Forest returns negative for anomalies, positive for normal
            if_score_normalized = 1 - (if_score + 0.5)  # Normalize to 0-1
            
            # Autoencoder reconstruction error
            ae_score = 0.0
            if TORCH_AVAILABLE and self.autoencoder:
                self.autoencoder.eval()
                with torch.no_grad():
                    X_tensor = torch.FloatTensor(X_scaled)
                    reconstructed = self.autoencoder(X_tensor)
                    ae_score = torch.mean((X_tensor - reconstructed) ** 2).item()
            
            # Combined score (weighted average)
            combined_score = 0.7 * if_score_normalized + 0.3 * min(ae_score * 10, 1.0)
            
            # Determine if anomaly
            is_anomaly = if_prediction == -1 or combined_score > 0.6
            
            if not is_anomaly:
                return None
            
            # Determine severity
            if combined_score >= 0.8:
                severity = "critical"
            elif combined_score >= 0.6:
                severity = "high"
            elif combined_score >= 0.4:
                severity = "medium"
            else:
                severity = "low"
            
            # Determine anomaly type
            if ae_score > if_score_normalized:
                anomaly_type = "ML-Based"
            else:
                anomaly_type = "Statistical"
            
            # Generate description
            description = self._generate_description(features, combined_score)
            
            return AnomalyResult(
                is_anomaly=True,
                score=combined_score,
                anomaly_type=anomaly_type,
                severity=severity,
                features={name: float(val) for name, val in zip(self.feature_names, features)},
                description=description,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error detecting anomaly: {e}")
            return None
    
    def _generate_description(self, features: np.ndarray, score: float) -> str:
        """Generate human-readable description of anomaly"""
        descriptions = []
        
        # Check packet rate
        if features[0] > 100:  # More than 100 packets per second
            descriptions.append("Unusually high packet rate")
        elif features[0] < 1:  # Less than 1 packet per second
            descriptions.append("Very low packet rate")
        
        # Check RSSI
        if features[1] < -85:
            descriptions.append("Very weak signal")
        elif features[1] > -50:
            descriptions.append("Unusually strong signal")
        
        # Check burstiness
        if features[7] > 2.0:
            descriptions.append("Highly bursty traffic pattern")
        
        # Check channel variance
        if features[5] > 10:
            descriptions.append("Unusual channel hopping")
        
        if descriptions:
            return "; ".join(descriptions)
        else:
            return f"Anomalous behavior detected (score: {score:.2f})"
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from Isolation Forest"""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return {}
        
        try:
            # Isolation Forest doesn't have direct feature importance
            # Use depth-based approximation
            return {name: 1.0 / len(self.feature_names) for name in self.feature_names}
        except:
            return {}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about trained models"""
        return {
            'is_trained': self.is_trained,
            'sklearn_available': SKLEARN_AVAILABLE,
            'torch_available': TORCH_AVAILABLE,
            'isolation_forest': self.isolation_forest is not None,
            'autoencoder': self.autoencoder is not None,
            'scaler': self.scaler is not None,
            'feature_count': len(self.feature_names),
            'training_samples': len(self.training_buffer)
        }
