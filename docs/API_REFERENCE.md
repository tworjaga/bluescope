# BlueScope API Reference

## Overview

BlueScope provides a comprehensive API for Bluetooth monitoring, capture, analysis, and export functionality.

## Core Modules

### Capture Manager (`backend.capture_manager`)

#### CaptureManager
Main class for managing Bluetooth capture operations.

```python
from backend.capture_manager import CaptureManager, CaptureBackend

# Create capture manager
manager = CaptureManager(backend=CaptureBackend.MOCK)

# Start capture
await manager.start_capture()

# Get devices
devices = manager.get_devices()

# Get packets
packets = manager.get_packets(limit=100)

# Stop capture
await manager.stop_capture()
```

**Methods:**
- `start_capture() -> bool`: Start packet capture
- `stop_capture()`: Stop packet capture
- `get_devices() -> List[BLEDevice]`: Get discovered devices
- `get_packets(limit=1000) -> List[BLEPacket]`: Get captured packets
- `get_statistics() -> Dict`: Get capture statistics

#### BLEDevice
Represents a Bluetooth Low Energy device.

```python
from backend.capture_manager import BLEDevice

device = BLEDevice(
    address="AA:BB:CC:DD:EE:01",
    name="Test Device",
    rssi=-65
)
```

**Attributes:**
- `address`: Device MAC address
- `name`: Device name
- `rssi`: Signal strength in dBm
- `packet_count`: Number of packets received
- `first_seen`: First detection timestamp
- `last_seen`: Last detection timestamp

#### BLEPacket
Represents a captured BLE packet.

```python
from backend.capture_manager import BLEPacket
from datetime import datetime

packet = BLEPacket(
    timestamp=datetime.now(),
    device_address="AA:BB:CC:DD:EE:01",
    packet_type="ADV_IND",
    channel=37,
    rssi=-65,
    data=b"\x02\x01\x06"
)
```

### ML Anomaly Detector (`analytics.anomaly_engine.ml_detector`)

#### MLAnomalyDetector
Machine learning-based anomaly detection.

```python
from analytics.anomaly_engine.ml_detector import MLAnomalyDetector

# Create detector
detector = MLAnomalyDetector(
    isolation_forest=True,
    autoencoder=True,
    statistical=True
)

# Train model
detector.train(training_data)

# Predict anomaly
result = detector.predict(sample_data)
```

**Methods:**
- `train(data) -> bool`: Train the ML model
- `predict(data) -> AnomalyResult`: Predict if data is anomalous
- `predict_batch(data) -> List[AnomalyResult]`: Batch prediction
- `save_model(path) -> bool`: Save trained model
- `load_model(path) -> bool`: Load trained model
- `set_threshold(threshold)`: Set anomaly threshold
- `get_feature_importance() -> Dict`: Get feature importance

#### AnomalyResult
Result of anomaly detection.

```python
from analytics.anomaly_engine.ml_detector import AnomalyResult

result = AnomalyResult(
    is_anomaly=True,
    anomaly_score=0.85,
    confidence=0.92,
    method="isolation_forest",
    features={"rssi_mean": -65},
    timestamp=datetime.now()
)
```

**Attributes:**
- `is_anomaly`: Whether the sample is anomalous
- `anomaly_score`: Anomaly score (0-1)
- `confidence`: Confidence level (0-1)
- `method`: Detection method used
- `features`: Extracted features
- `timestamp`: Detection timestamp

### Protocol Parser (`backend.protocol_parser`)

#### ProtocolParser
Parse BLE protocol stack.

```python
from backend.protocol_parser import get_protocol_parser

parser = get_protocol_parser()

# Parse packet
parsed = parser.parse_packet(data, timestamp=0.0, rssi=-65, channel=37)
```

**Methods:**
- `parse_packet(data, timestamp, rssi, channel) -> ParsedPacket`: Parse raw packet
- `parse_advertising_data(data) -> Dict`: Parse advertising data
- `parse_link_layer(data) -> Dict`: Parse Link Layer
- `parse_l2cap(data) -> Dict`: Parse L2CAP layer
- `parse_att(data) -> Dict`: Parse ATT layer

#### ParsedPacket
Parsed BLE packet with all protocol layers.

**Attributes:**
- `timestamp`: Packet timestamp
- `rssi`: Signal strength
- `channel`: BLE channel
- `ll_type`: Link Layer type
- `l2cap_cid`: L2CAP Channel ID
- `att_opcode`: ATT opcode
- `att_handle`: ATT handle
- `gatt_service_uuid`: GATT service UUID
- `adv_local_name`: Advertised device name
- `adv_service_uuids`: Advertised service UUIDs

### Filter Engine (`backend.filter_engine`)

#### FilterEngine
Advanced filtering for devices and packets.

```python
from backend.filter_engine import get_filter_engine, FilterField, FilterOperator

engine = get_filter_engine()

# Create filter condition
condition = engine.create_condition("device_rssi", ">", -70)

# Create filter group
group = engine.create_group([condition], "AND")

# Filter devices
filtered = engine.filter_devices(devices, group)
```

**Methods:**
- `create_condition(field, operator, value) -> FilterCondition`: Create condition
- `create_group(conditions, operator) -> FilterGroup`: Create group
- `filter_devices(devices, group) -> List[BLEDevice]`: Filter devices
- `filter_packets(packets, group) -> List[BLEPacket]`: Filter packets
- `quick_search(devices, term) -> List[BLEDevice]`: Quick search
- `save_filter(name, group)`: Save filter
- `load_filter(name) -> FilterGroup`: Load filter

### Export Manager (`backend.export_manager`)

#### ExportManager
Export data to various formats.

```python
from backend.export_manager import get_export_manager, ExportFormat

manager = get_export_manager()

# Export to CSV
manager.export_to_csv(devices, packets, "export.csv")

# Export to JSON
manager.export_to_json(devices, packets, "export.json")

# Export to PCAP
manager.export_to_pcap(packets, "capture.pcap")
```

**Methods:**
- `export_to_csv(devices, packets, path) -> bool`: Export to CSV
- `export_to_json(devices, packets, path) -> bool`: Export to JSON
- `export_to_pcap(packets, path) -> bool`: Export to PCAP
- `get_export_history() -> List[ExportRecord]`: Get export history
- `schedule_export(config)`: Schedule automatic export

### Session Manager (`backend.session_manager`)

#### SessionManager
Save and load capture sessions.

```python
from backend.session_manager import get_session_manager, SessionFormat

manager = get_session_manager()

# Save session
manager.save_session(devices, packets, "session.json", SessionFormat.JSON)

# Load session
devices, packets = manager.load_session("session.json")
```

**Methods:**
- `save_session(devices, packets, path, format) -> bool`: Save session
- `load_session(path) -> Tuple[List, List]`: Load session
- `enable_auto_save(interval_seconds)`: Enable auto-save
- `disable_auto_save()`: Disable auto-save

### Error Handler (`backend.error_handler`)

#### ErrorHandler
Centralized error handling.

```python
from backend.error_handler import get_error_handler, ErrorCategory, ErrorSeverity

handler = get_error_handler()

# Handle error
try:
    risky_operation()
except Exception as e:
    handler.handle_error(
        e,
        category=ErrorCategory.CAPTURE,
        severity=ErrorSeverity.ERROR,
        recoverable=True
    )
```

**Methods:**
- `handle_error(exception, category, severity, recoverable) -> bool`: Handle error
- `register_callback(category, callback)`: Register error callback
- `register_recovery_strategy(category, strategy)`: Register recovery
- `get_error_history() -> List[ErrorRecord]`: Get error history
- `get_statistics() -> Dict`: Get error statistics

### Performance Optimizer (`backend.performance_optimizer`)

#### PerformanceOptimizer
Monitor and optimize performance.

```python
from backend.performance_optimizer import get_performance_optimizer

optimizer = get_performance_optimizer()

# Get current metrics
metrics = optimizer.get_current_metrics()

# Get performance report
report = optimizer.get_performance_report()

# Optimize performance
optimizer.optimize_performance(level=1)
```

**Methods:**
- `get_current_metrics() -> PerformanceMetrics`: Get current metrics
- `record_metrics() -> PerformanceMetrics`: Record metrics
- `optimize_performance(level)`: Optimize performance
- `get_performance_report() -> Dict`: Get report
- `get_optimization_recommendations() -> List[str]`: Get recommendations

### Platform Utils (`backend.platform_utils`)

#### PlatformUtils
Cross-platform utilities.

```python
from backend.platform_utils import PlatformUtils

# Get platform
platform = PlatformUtils.get_platform()

# Get directories
config_dir = PlatformUtils.get_config_dir()
data_dir = PlatformUtils.get_data_dir()

# Get platform info
info = PlatformUtils.get_platform_info()
```

**Methods:**
- `get_platform() -> Platform`: Get current platform
- `is_windows() -> bool`: Check if Windows
- `is_linux() -> bool`: Check if Linux
- `is_macos() -> bool`: Check if macOS
- `get_config_dir() -> str`: Get config directory
- `get_data_dir() -> str`: Get data directory
- `get_cache_dir() -> str`: Get cache directory
- `get_log_dir() -> str`: Get log directory
- `ensure_directories()`: Ensure directories exist
- `get_platform_info() -> Dict`: Get platform info

## GUI Components

### Main Window (`frontend.ui.main_window`)

#### MainWindow
Main application window.

```python
from frontend.ui.main_window import MainWindow

window = MainWindow(config_path="config/settings.yaml")
window.show()
```

### Packet Inspector (`frontend.ui.packet_inspector`)

#### PacketInspectorDialog
Detailed packet inspection.

```python
from frontend.ui.packet_inspector import PacketInspectorDialog

dialog = PacketInspectorDialog(packet_data, parent=window)
dialog.exec()
```

### Session Replay (`frontend.ui.session_replay`)

#### SessionReplayDialog
Replay captured sessions.

```python
from frontend.ui.session_replay import SessionReplayDialog

dialog = SessionReplayDialog(packets, parent=window)
dialog.exec()
```

### Alert Notifications (`frontend.ui.alert_notification`)

#### AlertNotificationManager
System for alert notifications.

```python
from frontend.ui.alert_notification import AlertNotificationManager

manager = AlertNotificationManager(parent=window)
manager.show_notification("Alert Title", "Alert message", severity="high")
```

## Constants and Enums

### CaptureBackend
```python
class CaptureBackend(Enum):
    BLEAK = "bleak"      # Python Bleak library
    RUST = "rust"        # Rust capture agent
    MOCK = "mock"        # Mock data for testing
```

### ExportFormat
```python
class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    PCAP = "pcap"
```

### SessionFormat
```python
class SessionFormat(Enum):
    JSON = "json"
    PICKLE = "pickle"
    COMPRESSED = "compressed"
```

### ErrorCategory
```python
class ErrorCategory(Enum):
    CAPTURE = "capture"
    HARDWARE = "hardware"
    ML = "ml"
    GUI = "gui"
    NETWORK = "network"
    FILE = "file"
    MEMORY = "memory"
    UNKNOWN = "unknown"
```

### ErrorSeverity
```python
class ErrorSeverity(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
    FATAL = auto()
```

## Examples

### Basic Capture Example

```python
import asyncio
from backend.capture_manager import CaptureManager, CaptureBackend

async def main():
    # Create manager
    manager = CaptureManager(backend=CaptureBackend.MOCK)
    
    # Start capture
    await manager.start_capture()
    
    # Wait for data
    await asyncio.sleep(5)
    
    # Get results
    devices = manager.get_devices()
    packets = manager.get_packets()
    
    print(f"Found {len(devices)} devices, {len(packets)} packets")
    
    # Stop capture
    await manager.stop_capture()

asyncio.run(main())
```

### ML Anomaly Detection Example

```python
import numpy as np
from analytics.anomaly_engine.ml_detector import MLAnomalyDetector

# Create detector
detector = MLAnomalyDetector()

# Generate training data (normal behavior)
normal_data = np.random.randn(100, 5)
detector.train(normal_data)

# Test on new data
test_data = np.array([[0.1, -0.2, 0.3, -0.1, 0.2]])
result = detector.predict(test_data)

if result.is_anomaly:
    print(f"Anomaly detected! Score: {result.anomaly_score:.3f}")
```

### Export Example

```python
from backend.export_manager import get_export_manager, ExportFormat

manager = get_export_manager()

# Export to multiple formats
manager.export_to_csv(devices, packets, "export.csv")
manager.export_to_json(devices, packets, "export.json")
manager.export_to_pcap(packets, "capture.pcap")
```

## Error Handling

All APIs use exceptions for error handling:

```python
try:
    result = await manager.start_capture()
except CaptureError as e:
    print(f"Capture failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Thread Safety

Most APIs are thread-safe and can be called from multiple threads. However, GUI components should only be accessed from the main thread.

## Performance Considerations

- Use `get_packets(limit=N)` to limit memory usage
- Call `optimize_performance()` periodically for long-running captures
- Use `MemoryPool` for frequent object allocation
- Enable auto-save to prevent data loss

## Version Information

- **API Version**: 0.1.0
- **Python**: 3.11+
- **Last Updated**: January 2025

