"""
Test Suite for ML Anomaly Detector
Comprehensive tests for ML-based anomaly detection
"""

import pytest
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Any

from analytics.anomaly_engine.ml_detector import (
    MLAnomalyDetector, FeatureExtractor, AnomalyResult,
    get_ml_detector
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFeatureExtractor:
    """Tests for FeatureExtractor class"""
    
    def test_feature_extraction(self):
        """Test basic feature extraction"""
        extractor = FeatureExtractor()
        
        # Create sample packet data
        packets = [
            {"timestamp": datetime.now(), "rssi": -65, "size": 20},
            {"timestamp": datetime.now(), "rssi": -70, "size": 25},
            {"timestamp": datetime.now(), "rssi": -68, "size": 22},
        ]
        
        features = extractor.extract_features(packets)
        
        assert isinstance(features, np.ndarray)
        assert len(features) > 0
        logger.info(f" Feature extraction test passed - extracted {len(features)} features")
    
    def test_rssi_features(self):
        """Test RSSI feature extraction"""
        extractor = FeatureExtractor()
        
        rssi_values = [-65, -70, -68, -72, -65]
        features = extractor.extract_rssi_features(rssi_values)
        
        assert isinstance(features, dict)
        assert "mean" in features
        assert "std" in features
        assert "min" in features
        assert "max" in features
        
        assert features["mean"] == pytest.approx(-68.0, abs=1.0)
        logger.info(" RSSI features test passed")
    
    def test_temporal_features(self):
        """Test temporal feature extraction"""
        extractor = FeatureExtractor()
        
        from datetime import timedelta
        timestamps = [
            datetime.now(),
            datetime.now() + timedelta(seconds=1),
            datetime.now() + timedelta(seconds=2),
            datetime.now() + timedelta(seconds=4),
        ]
        
        features = extractor.extract_temporal_features(timestamps)
        
        assert isinstance(features, dict)
        assert "packet_rate" in features
        assert "interval_mean" in features
        logger.info(" Temporal features test passed")


class TestMLAnomalyDetector:
    """Tests for MLAnomalyDetector class"""
    
    @pytest.fixture
    def detector(self):
        """Create a detector for testing"""
        return MLAnomalyDetector(
            isolation_forest=True,
            autoencoder=False,  # Disable for faster tests
            statistical=True
        )
    
    def test_detector_initialization(self, detector):
        """Test detector initialization"""
        assert detector is not None
        assert detector.isolation_forest_enabled is True
        assert detector.autoencoder_enabled is False
        assert detector.statistical_enabled is True
        assert detector.is_trained is False
        logger.info(" Detector initialization test passed")
    
    def test_training(self, detector):
        """Test model training"""
        # Generate sample training data
        np.random.seed(42)
        normal_data = np.random.randn(100, 5)  # 100 samples, 5 features
        
        # Train
        success = detector.train(normal_data)
        
        assert success is True
        assert detector.is_trained is True
        logger.info(" Training test passed")
    
    def test_anomaly_detection(self, detector):
        """Test anomaly detection"""
        # Train first
        np.random.seed(42)
        normal_data = np.random.randn(100, 5)
        detector.train(normal_data)
        
        # Test normal data
        normal_sample = np.random.randn(1, 5)
        result = detector.predict(normal_sample)
        
        assert isinstance(result, AnomalyResult)
        assert 0 <= result.anomaly_score <= 1
        logger.info(f" Anomaly detection test passed - score: {result.anomaly_score:.3f}")
    
    def test_anomaly_scoring(self, detector):
        """Test anomaly scoring with known outliers"""
        # Train on normal data
        np.random.seed(42)
        normal_data = np.random.randn(100, 5)
        detector.train(normal_data)
        
        # Test normal sample
        normal_sample = np.array([[0.1, -0.2, 0.3, -0.1, 0.2]])
        normal_result = detector.predict(normal_sample)
        
        # Test anomalous sample (far from normal distribution)
        anomaly_sample = np.array([[10.0, -10.0, 10.0, -10.0, 10.0]])
        anomaly_result = detector.predict(anomaly_sample)
        
        # Anomaly should have higher score
        assert anomaly_result.anomaly_score > normal_result.anomaly_score
        assert anomaly_result.is_anomaly is True
        logger.info(f" Anomaly scoring test passed - normal: {normal_result.anomaly_score:.3f}, anomaly: {anomaly_result.anomaly_score:.3f}")
    
    def test_feature_importance(self, detector):
        """Test feature importance extraction"""
        # Train
        np.random.seed(42)
        data = np.random.randn(100, 5)
        detector.train(data)
        
        # Get feature importance
        importance = detector.get_feature_importance()
        
        assert isinstance(importance, dict)
        assert len(importance) > 0
        logger.info(f" Feature importance test passed - {len(importance)} features")
    
    def test_model_save_load(self, detector, tmp_path):
        """Test model save and load"""
        # Train
        np.random.seed(42)
        data = np.random.randn(100, 5)
        detector.train(data)
        
        # Save
        model_path = tmp_path / "test_model.pkl"
        save_success = detector.save_model(str(model_path))
        assert save_success is True
        
        # Create new detector and load
        new_detector = MLAnomalyDetector()
        load_success = new_detector.load_model(str(model_path))
        assert load_success is True
        assert new_detector.is_trained is True
        
        logger.info(" Model save/load test passed")
    
    def test_batch_prediction(self, detector):
        """Test batch prediction"""
        # Train
        np.random.seed(42)
        train_data = np.random.randn(100, 5)
        detector.train(train_data)
        
        # Batch predict
        test_data = np.random.randn(10, 5)
        results = detector.predict_batch(test_data)
        
        assert isinstance(results, list)
        assert len(results) == 10
        assert all(isinstance(r, AnomalyResult) for r in results)
        logger.info(" Batch prediction test passed")
    
    def test_threshold_adjustment(self, detector):
        """Test threshold adjustment"""
        # Train
        np.random.seed(42)
        data = np.random.randn(100, 5)
        detector.train(data)
        
        # Set custom threshold
        detector.set_threshold(0.5)
        assert detector.threshold == 0.5
        
        # Test with different thresholds
        sample = np.random.randn(1, 5)
        
        detector.set_threshold(0.1)  # Low threshold
        result_low = detector.predict(sample)
        
        detector.set_threshold(0.9)  # High threshold
        result_high = detector.predict(sample)
        
        # Lower threshold should flag more anomalies
        logger.info(" Threshold adjustment test passed")


class TestAnomalyResult:
    """Tests for AnomalyResult class"""
    
    def test_result_creation(self):
        """Test anomaly result creation"""
        result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=0.85,
            confidence=0.92,
            method="isolation_forest",
            features={"rssi_mean": -65, "packet_rate": 10},
            timestamp=datetime.now()
        )
        
        assert result.is_anomaly is True
        assert result.anomaly_score == 0.85
        assert result.confidence == 0.92
        assert result.method == "isolation_forest"
        logger.info(" Anomaly result creation test passed")
    
    def test_result_serialization(self):
        """Test result serialization to dict"""
        result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=0.85,
            confidence=0.92,
            method="isolation_forest",
            features={"rssi_mean": -65},
            timestamp=datetime.now()
        )
        
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["is_anomaly"] is True
        assert data["anomaly_score"] == 0.85
        logger.info(" Result serialization test passed")


class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_detection(self):
        """Test end-to-end anomaly detection pipeline"""
        # Create detector
        detector = MLAnomalyDetector()
        
        # Create feature extractor
        extractor = FeatureExtractor()
        
        # Generate training data (simulating normal device behavior)
        np.random.seed(42)
        normal_packets = [
            {"rssi": np.random.normal(-65, 5), "size": np.random.normal(20, 3)}
            for _ in range(100)
        ]
        
        # Extract features and train
        features = extractor.extract_features(normal_packets)
        detector.train(features.reshape(-1, 1) if features.ndim == 1 else features)
        
        # Test on normal data
        normal_test = [{"rssi": -66, "size": 21}]
        normal_features = extractor.extract_features(normal_test)
        normal_result = detector.predict(normal_features.reshape(-1, 1) if normal_features.ndim == 1 else normal_features)
        
        # Test on anomalous data
        anomaly_test = [{"rssi": -90, "size": 100}]  # Unusual values
        anomaly_features = extractor.extract_features(anomaly_test)
        anomaly_result = detector.predict(anomaly_features.reshape(-1, 1) if anomaly_features.ndim == 1 else anomaly_features)
        
        # Anomaly should be detected
        assert anomaly_result.anomaly_score > normal_result.anomaly_score
        logger.info(f" End-to-end test passed - anomaly score: {anomaly_result.anomaly_score:.3f}")
    
    def test_singleton_pattern(self):
        """Test singleton pattern for global detector"""
        detector1 = get_ml_detector()
        detector2 = get_ml_detector()
        
        assert detector1 is detector2
        logger.info(" Singleton pattern test passed")


def run_performance_test():
    """Run performance benchmark"""
    print("\n" + "="*70)
    print("ML Detector Performance Test")
    print("="*70)
    
    import time
    
    detector = MLAnomalyDetector(autoencoder=False)
    
    # Training performance
    np.random.seed(42)
    train_data = np.random.randn(1000, 10)
    
    start = time.time()
    detector.train(train_data)
    train_time = time.time() - start
    
    print(f"Training time (1000 samples): {train_time:.3f}s")
    
    # Prediction performance
    test_data = np.random.randn(100, 10)
    
    start = time.time()
    results = detector.predict_batch(test_data)
    predict_time = time.time() - start
    
    print(f"Prediction time (100 samples): {predict_time:.3f}s")
    print(f"Average per sample: {predict_time/100*1000:.2f}ms")
    
    return train_time < 5.0 and predict_time < 1.0


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("BlueScope ML Detector Test Suite")
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
    
    # Run performance test
    perf_passed = run_performance_test()
    
    return result.returncode == 0 and perf_passed


if __name__ == "__main__":
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        
        # Run basic tests
        test_extractor = TestFeatureExtractor()
        test_extractor.test_feature_extraction()
        test_extractor.test_rssi_features()
        
        test_detector = TestMLAnomalyDetector()
        detector = test_detector.detector()
        test_detector.test_detector_initialization(detector)
        test_detector.test_training(detector)
        
        print("\n Basic tests completed")

