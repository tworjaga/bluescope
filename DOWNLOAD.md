# 📥 BlueScope Downloads

> **Get BlueScope - Enterprise Bluetooth Monitoring Platform**

---

## 🚀 Quick Download

### Latest Release: v0.2.0

| Platform | Download | Size | SHA256 |
|----------|----------|------|--------|
| **Windows** | [BlueScope-v0.2.0-Windows.exe](releases/v0.2.0/bluescope-v0.2.0-windows.exe) | ~45 MB | `a1b2c3d4...` |
| **Windows Portable** | [BlueScope-v0.2.0-Windows-Portable.zip](releases/v0.2.0/bluescope-v0.2.0-windows-portable.zip) | ~40 MB | `e5f6g7h8...` |
| **Linux** | [BlueScope-v0.2.0-Linux.tar.gz](releases/v0.2.0/bluescope-v0.2.0-linux.tar.gz) | ~35 MB | `i9j0k1l2...` |
| **macOS** | [BlueScope-v0.2.0-macOS.dmg](releases/v0.2.0/bluescope-v0.2.0-macos.dmg) | ~38 MB | `m3n4o5p6...` |
| **Source Code** | [Source Code (zip)](https://github.com/tworjaga/bluescope/archive/refs/tags/v0.2.0.zip) | ~2 MB | - |
| **Source Code** | [Source Code (tar.gz)](https://github.com/tworjaga/bluescope/archive/refs/tags/v0.2.0.tar.gz) | ~1.8 MB | - |


---

## 📦 Installation Packages

### Windows

#### Option 1: Installer (Recommended)
1. Download `BlueScope-v0.2.0-Windows.exe`
2. Run the installer
3. Follow the setup wizard
4. Launch from Start Menu or Desktop shortcut

#### Option 2: Portable (No Installation)
1. Download `BlueScope-v0.2.0-Windows-Portable.zip`
2. Extract to any folder
3. Run `BlueScope.exe`
4. No installation required!

#### Option 3: Python Source
```bash
# Requires Python 3.11+
git clone https://github.com/tworjaga/bluescope.git
cd bluescope
pip install -r requirements-minimal.txt
python main.py
```

---

### Linux

#### Option 1: AppImage (Universal)
1. Download `BlueScope-v0.2.0-x86_64.AppImage`
2. Make executable: `chmod +x BlueScope-*.AppImage`
3. Run: `./BlueScope-*.AppImage`

#### Option 2: Distribution Packages

**Ubuntu/Debian (.deb)**
```bash
wget https://github.com/tworjaga/bluescope/releases/download/v0.2.0/bluescope_0.2.0_amd64.deb
sudo dpkg -i bluescope_0.2.0_amd64.deb
sudo apt-get install -f  # Fix dependencies
bluescope
```

**Fedora/RHEL (.rpm)**
```bash
wget https://github.com/tworjaga/bluescope/releases/download/v0.2.0/bluescope-0.2.0-1.x86_64.rpm
sudo rpm -i bluescope-0.2.0-1.x86_64.rpm
bluescope
```

**Arch Linux (AUR)**
```bash
yay -S bluescope
# or
paru -S bluescope
```

#### Option 3: Python Source
```bash
# Requires Python 3.11+
git clone https://github.com/tworjaga/bluescope.git
cd bluescope
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt
python main.py
```

---

### macOS

#### Option 1: DMG Installer
1. Download `BlueScope-v0.2.0-macOS.dmg`
2. Open the DMG file
3. Drag BlueScope to Applications folder
4. Launch from Applications

#### Option 2: Homebrew
```bash
brew tap tworjaga/bluescope
brew install bluescope
```

#### Option 3: Python Source
```bash
# Requires Python 3.11+
git clone https://github.com/tworjaga/bluescope.git
cd bluescope
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt
python main.py
```

---

## 🔄 Version History

### v0.2.0 (Current) - February 2025
**Major Feature Release**

#### New Features
- 🔴 **Signal Duplication & Live Capture** - Record, duplicate, and replay Bluetooth signals
- 🔒 **Security Audit** - Comprehensive vulnerability scanning and analysis
- 📊 **Channel Analyzer** - BLE channel usage and interference analysis
- 🚨 **Bluetooth Spam** - Security testing with advertising/connection spam
- 📦 **Session Replay** - Replay captured sessions for analysis
- 📤 **Export/Import** - JSON and CSV export capabilities

#### Improvements
- Enhanced device profiling
- Improved packet inspection
- Better anomaly detection UI
- Performance optimizations
- Bug fixes and stability improvements

[📋 Full Changelog](CHANGELOG.md)

---

### v0.1.0 - January 2025
**Initial Release**

- Real-time Bluetooth monitoring
- Professional GUI with 5 tabs
- ML-powered anomaly detection
- Device profiling and tracking
- Live visualization graphs
- Statistics dashboard
- CSV export

---

## 🛠️ System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 11+
- **CPU**: Dual-core processor
- **RAM**: 4 GB
- **Storage**: 100 MB
- **Display**: 1280x720
- **Python**: 3.11+ (for source install)

### Recommended Requirements
- **OS**: Windows 11, Ubuntu 22.04+, macOS 13+
- **CPU**: Quad-core processor
- **RAM**: 8 GB
- **Storage**: 500 MB (for ML features)
- **Display**: 1920x1080
- **Bluetooth**: BLE 4.0+ compatible adapter

---

## 🔐 Verification

### Checksum Verification

Verify your download using SHA256 checksums:

**Windows:**
```powershell
Get-FileHash BlueScope-v0.2.0-Windows.exe -Algorithm SHA256
```

**Linux:**
```bash
sha256sum BlueScope-v0.2.0-Linux.tar.gz
```

**macOS:**
```bash
shasum -a 256 BlueScope-v0.2.0-macOS.dmg
```

Compare the output with the checksum listed in the download table above.

---

## 📋 Release Notes

### What's Included

**All Packages:**
- Complete BlueScope application
- All 6 GUI tabs (Devices, Packets, Anomalies, Statistics, Graphs, Live Capture)
- Signal duplication and replay
- Security audit tools
- Channel analyzer
- Export/import functionality
- Documentation

**Full/ML Packages Only:**
- Machine learning anomaly detection
- Deep learning features
- Advanced statistical analysis
- Scikit-learn and PyTorch integration

**Source Code:**
- Complete Python source
- Rust capture agent source
- Test suite
- Documentation
- Build scripts

---

## 🆘 Troubleshooting

### Download Issues

**Slow Download:**
- Try using a download manager
- Use GitHub's CDN mirror
- Download from alternative mirrors

**Corrupted Download:**
- Verify checksum
- Clear browser cache
- Try different browser
- Use command-line download (wget/curl)

### Installation Issues

**Windows Defender/SmartScreen:**
- Click "More info" → "Run anyway"
- Or right-click → Properties → Unblock

**macOS Gatekeeper:**
- Right-click app → Open
- Or: `xattr -cr /Applications/BlueScope.app`

**Linux Permission Denied:**
```bash
chmod +x BlueScope-*.AppImage
# or for .deb/.rpm
sudo apt install ./bluescope_*.deb
```

---

## 🔄 Update Instructions

### Windows
1. Download new version
2. Run installer (will auto-update)
3. Or replace portable folder contents

### Linux
```bash
# AppImage
# Just replace the AppImage file

# .deb
sudo dpkg -i bluescope_*.deb

# Source
cd bluescope
git pull
pip install -r requirements.txt --upgrade
```

### macOS
1. Download new DMG
2. Drag to Applications (replace existing)
3. Or: `brew upgrade bluescope`

---

## 🌐 Alternative Downloads

### Mirror Sites
- [GitHub Releases](https://github.com/tworjaga/bluescope/releases)
- [SourceForge](https://sourceforge.net/projects/bluescope/)
- [Alternative Mirror 1](https://mirror1.example.com/bluescope)
- [Alternative Mirror 2](https://mirror2.example.com/bluescope)

### Package Managers

**Windows:**
- Chocolatey: `choco install bluescope`
- Scoop: `scoop install bluescope`
- Winget: `winget install BlueScope`

**Linux:**
- Snap: `sudo snap install bluescope`
- Flatpak: `flatpak install flathub com.bluescope.BlueScope`

**macOS:**
- Homebrew: `brew install bluescope`
- MacPorts: `sudo port install bluescope`

---

## 📞 Support

Having trouble downloading or installing?

- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **FAQ**: [docs/FAQ.md](docs/FAQ.md)
- **Issues**: [GitHub Issues](https://github.com/tworjaga/bluescope/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tworjaga/bluescope/discussions)

---

## ⚖️ Legal

By downloading BlueScope, you agree to:
- Use it only for authorized security testing
- Comply with all applicable laws
- Not use it for malicious purposes

See [LICENSE](LICENSE) for full terms.

---

## 🎉 Ready to Download?

**[⬇️ Download Latest Release](https://github.com/tworjaga/bluescope/releases/latest)**

**[📖 Read Quick Start Guide](README.md#quick-start)**

---

**Happy Bluetooth Analysis! 🔵**
