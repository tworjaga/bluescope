# 🔵 BlueScope

> **Enterprise Bluetooth Monitoring, Security Analysis & Signal Manipulation Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.2.0-success.svg)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

<div align="center">
  <img src="https://visitor-badge.laobi.icu/badge?page_id=tworjaga.bluescope&"  />
</div>


A professional-grade Bluetooth monitoring and analysis tool with ML-powered anomaly detection, real-time visualization, signal duplication, security auditing, and comprehensive device profiling capabilities.

![BlueScope Screenshot](docs/screenshot.png)

---

## Features

### Core Capabilities
- **Real-time Bluetooth Monitoring** - Capture and analyze BLE traffic with live updates
- **Professional GUI** - Dark-themed interface with 6 functional tabs
- **ML-Powered Analytics** - Anomaly detection using Isolation Forest & Autoencoders
- **Device Profiling** - Comprehensive device behavior analysis
- **Live Visualization** - Real-time graphs for traffic and RSSI
- **Statistics Dashboard** - Detailed metrics and performance indicators

### Signal Duplication & Live Capture
- **Signal Recording** - Capture and store Bluetooth signals in real-time
- **Signal Duplication** - Replay signals with multiple modes (immediate, delayed, burst, random)
- **Live Signal Table** - Real-time visualization of captured signals with RSSI color-coding
- **Export/Import** - Save signal captures to JSON for later analysis
- **Signal Replay** - Replicate captured traffic patterns for testing

### Security Analysis
- **Device Scanner** - Discover and profile nearby Bluetooth devices
- **Security Audit** - Comprehensive vulnerability assessment
- **Channel Analyzer** - Analyze BLE channel usage and interference
- **Faraday Simulator** - Educational simulation of RF isolation effects
- **Vulnerability Detection** - Identify known vulnerable device signatures

### Bluetooth Spam (Security Testing)
- **Advertising Spam** - Flood advertising channels (simulation mode)
- **Connection Request Spam** - Test device resilience
- **L2CAP/ATT Packet Spam** - Protocol-level testing
- **Real Transmission** - Linux-only with root and proper hardware

### Analytics Features
- **Behavior Engine** - Pattern detection and baseline profiling
- **Anomaly Detection** - Statistical and ML-based anomaly identification
- **Device Tracking** - Monitor multiple devices simultaneously
- **Packet Analysis** - Deep packet inspection and protocol analysis
- **Session Replay** - Replay captured sessions for analysis

### User Interface
- **6 Tabs**: Devices, Packets, Anomalies, Statistics, Graphs, Live Capture
- **Dark Theme** - Professional VS Code-inspired design
- **Real-time Updates** - Live data refresh every second
- **Search & Filter** - Quick data filtering and search
- **Export Capabilities** - CSV and JSON export for further analysis

---

## Quick Start

### Prerequisites
- **Python 3.11+** (Python 3.14 recommended)
- **Windows 10/11** (primary support), Linux, macOS
- **4GB RAM** minimum (8GB recommended)
- **100MB** disk space

### Installation

#### Method 1: One-Click Launch (Easiest)
```bash
# Clone the repository
git clone https://github.com/tworjaga/bluescope.git
cd bluescope

# Run the launcher
start.bat
```

#### Method 2: Manual Setup
```bash
# Clone the repository
git clone https://github.com/tworjaga/bluescope.git
cd bluescope

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements-minimal.txt

# Launch application
python main.py
```

#### Method 3: Full Installation with All Features
```bash
# Install all dependencies including ML and security features
pip install -r requirements.txt

# Launch
python main.py
```

---

## Usage Guide

### Starting BlueScope
1. **Launch the application**:
   - Run `start.bat`, or
   - Run `python main.py`

2. **Start Capture**:
   - Click the green "▶ Start Capture" button
   - Watch real-time data populate all panels

3. **Explore Features**:
   - **Devices Tab**: View discovered Bluetooth devices
   - **Packets Tab**: Inspect captured packets
   - **Anomalies Tab**: Review ML-detected anomalies
   - **Statistics Panel**: Monitor real-time metrics
   - **Graphs**: Visualize traffic and RSSI data
   - **Live Capture**: Record and duplicate signals

### Security Analysis
1. **Open Security Audit**: Tools > Security Audit (Ctrl+Shift+A)
2. **Run Device Scanner**: Click "Start Security Scan"
3. **Analyze Channels**: Switch to "Channel Analyzer" tab
4. **View Results**: Review vulnerabilities and recommendations

### Signal Duplication
1. **Open Live Capture**: Switch to "Live Capture" tab
2. **Start Recording**: Click "Start Recording"
3. **Configure Duplication**: Set mode (immediate/delayed/burst/random)
4. **Start Duplication**: Click "▶ Start Duplication"
5. **Replay Signals**: Use "Replay" controls

### Key Controls
- **Ctrl+P**: Start/Stop capture
- **Ctrl+Shift+A**: Security Audit
- **Ctrl+Shift+D**: Signal Duplication
- **Ctrl+Shift+S**: Bluetooth Spam (Security Testing)
- **Ctrl+S**: Save session
- **Ctrl+E**: Export to CSV
- **Ctrl+R**: Reset statistics
- **F5**: Refresh view
- **F11**: Toggle fullscreen

---

## Architecture

```
bluescope/
├── main.py                      # Application entry point
├── frontend/                    # GUI components
│   ├── ui/                     # UI widgets
│   │   ├── main_window.py      # Main application window
│   │   ├── device_table.py     # Device listing table
│   │   ├── packet_table.py     # Packet inspection table
│   │   ├── statistics_panel.py # Real-time statistics
│   │   ├── graphs.py           # Traffic & RSSI graphs
│   │   ├── anomaly_panel.py    # Anomaly display
│   │   ├── live_capture_view.py # Signal duplication UI
│   │   ├── packet_inspector.py # Deep packet inspection
│   │   ├── session_replay.py   # Session replay controls
│   │   ├── export_config_dialog.py # Export configuration
│   │   └── alert_notification.py # Alert system
│   └── themes/                 # UI themes
│       └── dark_theme.py       # Dark theme styling
├── backend/                     # Core backend modules
│   ├── capture_manager.py      # Bluetooth capture engine
│   ├── signal_duplicator.py   # Signal recording & replay
│   ├── bluetooth_security.py  # Security analysis tools
│   ├── bluetooth_spam.py      # Security testing (simulation)
│   ├── linux_bluetooth_tx.py  # Real transmission (Linux)
│   ├── export_manager.py      # Data export functionality
│   ├── session_manager.py     # Session management
│   ├── protocol_parser.py     # BLE protocol parsing
│   ├── filter_engine.py       # Packet filtering
│   ├── ml_integration.py      # Machine learning integration
│   ├── multi_capture_manager.py # Multi-device capture
│   ├── advanced_protocols.py  # Advanced protocol support
│   ├── plugin_system.py       # Plugin architecture
│   ├── error_handler.py       # Error handling
│   ├── performance_optimizer.py # Performance optimization
│   └── platform_utils.py      # Platform-specific utilities
├── analytics/                   # Analytics engines
│   ├── behavior_engine/       # Behavior analysis
│   │   └── main.py
│   └── anomaly_engine/        # Anomaly detection
│       ├── main.py
│       └── ml_detector.py
├── agents/                      # Capture agents
│   └── bt-capture/            # Rust-based capture agent
│       └── src/
├── config/                      # Configuration files
│   └── settings.yaml
├── docs/                        # Documentation
│   └── API_REFERENCE.md
├── exports/                     # Export directory
├── logs/                        # Application logs
└── tests/                       # Test suite
```

---

## Configuration

Edit `config/settings.yaml` to customize:

```yaml
app:
  name: "BlueScope"
  version: "0.2.0"
  log_level: "INFO"

capture:
  device: "auto"
  buffer_size: 10000
  update_interval: 1000
  backend: "mock"  # Options: mock, bleak, rust

analytics:
  behavior_engine:
    enabled: true
    baseline_window: 86400
  anomaly_engine:
    enabled: true
    threshold: 2.5

signal_duplication:
  enabled: true
  auto_record: false
  default_mode: "immediate"

security:
  auto_scan: false
  vulnerability_check: true

ui:
  theme: "dark"
  update_rate: 1000
  max_table_rows: 10000
```

---

## Dependencies

### Core (Minimal Install)
- **PyQt6** (>=6.6.0) - GUI framework
- **NumPy** (>=1.26.0) - Data processing
- **python-dotenv** (>=1.0.0) - Environment variables
- **PyYAML** (>=6.0.1) - Configuration management

### ML & Analytics (Full Install)
- **scikit-learn** (>=1.8.0) - Machine learning algorithms
- **PyTorch** (>=2.9.0) - Deep learning framework
- **scipy** (>=1.16.0) - Scientific computing

### Security & Capture (Optional)
- **bleak** (>=0.21.0) - Cross-platform BLE library
- **pyusb** (>=1.2.1) - USB device access

See `requirements.txt` for complete list.

---

## Testing

Run the verification script:
```bash
python verify_installation.py
```

Run backend tests:
```bash
python backend/bluetooth_security.py
```

Expected output:
```
============================================================
Bluetooth Security Module Test
============================================================
1. Testing Bluetooth Scanner...
   Devices found: 4
   Security issues: 10
   Critical devices: 2

2. Testing Channel Analyzer...
   Total packets: 33
   Interference detected: False

3. Testing Faraday Simulator...
   Devices blocked: 4
   Remaining: 0

4. Testing Full Security Audit...
   Risk Level: LOW
   Key Findings: 4

✓ All security module tests passed!
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/tworjaga/bluescope.git
cd bluescope

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Run tests
pytest

# Format code
black .
```

---

## Legal Notice

**For Authorized Security Testing Only**

BlueScope includes security testing features (Bluetooth Spam, Signal Duplication) that are intended for:
- Authorized penetration testing
- Security research in controlled environments
- Educational purposes
- Testing your own devices

**Do not use these features to:**
- Attack networks or devices without explicit permission
- Disrupt public Bluetooth services
- Violate any laws or regulations
- Harass or spy on individuals

The authors are not responsible for misuse of this software. Always ensure you have proper authorization before testing any Bluetooth systems.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **PyQt6** - For the excellent GUI framework
- **scikit-learn** - For ML algorithms
- **PyTorch** - For deep learning capabilities
- **bleak** - For cross-platform BLE support
- **Community** - For feedback and contributions

---

## Support

- **Issues**: [GitHub Issues](https://github.com/tworjaga/bluescope/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tworjaga/bluescope/discussions)
- **Email**: tworjaga@example.com


---

## Roadmap

### Version 0.2.0 (Current)
- [x] Signal Duplication & Live Capture
- [x] Security Audit & Device Scanner
- [x] Channel Analyzer
- [x] Bluetooth Spam (Security Testing)
- [x] Session Replay
- [x] Export/Import functionality

### Version 0.3.0 (Planned)
- [ ] Real Bluetooth hardware integration
- [ ] Advanced protocol parsers (BLE 5.0, Mesh)
- [ ] Multi-device simultaneous capture
- [ ] Cloud synchronization
- [ ] Advanced ML models
- [ ] Plugin system

### Version 1.0.0 (Future)
- [ ] Production-ready release
- [ ] Complete hardware support (Ubertooth, HackRF)
- [ ] Full documentation
- [ ] Enterprise features
- [ ] Comprehensive testing suite

---

## Project Status

- **Version**: 0.2.0
- **Status**: Production Ready
- **Last Updated**: March 2025
- **Python**: 3.11+
- **Platform**: Windows (primary), Linux, macOS

---

## Star History

If you find this project useful, please consider giving it a star

---




