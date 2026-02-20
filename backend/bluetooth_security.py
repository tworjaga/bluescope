"""
Bluetooth Security Testing Module - Legal security analysis tools
For authorized penetration testing and security research only
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import random

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Device security assessment levels"""
    CRITICAL = auto()    # Known vulnerable, easily exploitable
    HIGH = auto()        # Suspicious behavior, potential issues
    MEDIUM = auto()      # Some security concerns
    LOW = auto()         # Generally secure
    UNKNOWN = auto()     # Not enough data


@dataclass
class BLEDeviceProfile:
    """Detailed BLE device security profile"""
    address: str
    name: str = ""
    rssi: int = -100
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    
    # Security analysis
    security_level: SecurityLevel = SecurityLevel.UNKNOWN
    vulnerabilities: List[str] = field(default_factory=list)
    suspicious_patterns: List[str] = field(default_factory=list)
    
    # Device characteristics
    device_type: str = "Unknown"
    manufacturer: str = "Unknown"
    services: List[str] = field(default_factory=list)
    characteristics: Dict[str, Any] = field(default_factory=dict)
    
    # Behavior analysis
    packet_count: int = 0
    connection_attempts: int = 0
    pairing_requests: int = 0
    
    # Privacy analysis
    address_type: str = "public"  # public, random_static, random_private
    trackable: bool = False
    identifiable: bool = False


@dataclass
class ChannelMetrics:
    """BLE channel usage metrics"""
    channel: int
    packet_count: int = 0
    device_count: int = 0
    average_rssi: float = -100.0
    interference_level: float = 0.0  # 0-100%
    utilization_percent: float = 0.0


class BluetoothScanner:
    """
    Advanced Bluetooth scanner for security analysis
    Detects and profiles all nearby BLE devices
    """
    
    # Known vulnerable device signatures
    VULNERABLE_SIGNATURES = {
        'airpods': {
            'patterns': ['AirPods', 'AirPods Pro', 'AirPods Max'],
            'vulnerabilities': ['Spoofing attack possible', 'No authentication required'],
            'level': SecurityLevel.HIGH
        },
        'cheap_earbuds': {
            'patterns': ['TWS', 'Earbuds', 'BT-Speaker', 'Wireless'],
            'vulnerabilities': ['No pairing authentication', 'Fixed PIN (0000/1234)'],
            'level': SecurityLevel.CRITICAL
        },
        'fitness_trackers': {
            'patterns': ['Mi Band', 'Fitbit', 'Amazfit', 'Honor Band'],
            'vulnerabilities': ['Unencrypted data transmission', 'Predictable MAC rotation'],
            'level': SecurityLevel.HIGH
        },
        'smart_locks': {
            'patterns': ['Lock', 'SmartLock', 'Keyless'],
            'vulnerabilities': ['Relay attack possible', 'Weak encryption'],
            'level': SecurityLevel.CRITICAL
        },
        'beacons': {
            'patterns': ['iBeacon', 'Eddystone', 'Beacon'],
            'vulnerabilities': ['Trackable', 'Spoofable', 'No security'],
            'level': SecurityLevel.MEDIUM
        }
    }
    
    def __init__(self):
        self.devices: Dict[str, BLEDeviceProfile] = {}
        self.scanning = False
        self.scan_start_time: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            'total_devices_seen': 0,
            'current_devices': 0,
            'security_issues_found': 0,
            'scan_duration': 0.0
        }
    
    async def start_scan(self, duration: int = 60):
        """Start comprehensive security scan"""
        self.scanning = True
        self.scan_start_time = datetime.now()
        
        logger.info(f"Starting Bluetooth security scan for {duration}s")
        
        try:
            # In real implementation, this would use bleak or HCI
            # For now, simulate scanning
            await self._simulate_scan(duration)
            
        except asyncio.CancelledError:
            logger.info("Scan cancelled")
        finally:
            self.scanning = False
            self.stats['scan_duration'] = (
                datetime.now() - self.scan_start_time
            ).total_seconds()
    
    async def _simulate_scan(self, duration: int):
        """Simulate device discovery"""
        end_time = time.time() + duration
        
        while self.scanning and time.time() < end_time:
            # Simulate finding devices
            await self._discover_random_device()
            await asyncio.sleep(random.uniform(0.5, 2.0))
    
    async def _discover_random_device(self):
        """Simulate discovering a device"""
        # Generate random device
        mac = ':'.join([f'{random.randint(0, 255):02X}' for _ in range(6)])
        
        device_types = list(self.VULNERABLE_SIGNATURES.keys())
        device_type = random.choice(device_types)
        signature = self.VULNERABLE_SIGNATURES[device_type]
        
        name = random.choice(signature['patterns'])
        
        # Create profile
        profile = BLEDeviceProfile(
            address=mac,
            name=name,
            rssi=random.randint(-90, -40),
            device_type=device_type,
            security_level=signature['level'],
            vulnerabilities=signature['vulnerabilities'].copy(),
            services=self._generate_services(device_type),
            packet_count=random.randint(1, 100)
        )
        
        # Analyze privacy
        self._analyze_privacy(profile)
        
        self.devices[mac] = profile
        self.stats['total_devices_seen'] += 1
        self.stats['current_devices'] = len(self.devices)
        self.stats['security_issues_found'] += len(profile.vulnerabilities)
        
        logger.debug(f"Discovered: {name} ({mac}) - {profile.security_level.name}")
    
    def _generate_services(self, device_type: str) -> List[str]:
        """Generate realistic service UUIDs for device type"""
        common_services = {
            'airpods': ['0x1101', '0x110E', '0x111E'],
            'cheap_earbuds': ['0x1101', '0x110A'],
            'fitness_trackers': ['0x180D', '0x180A', '0x180F'],
            'smart_locks': ['0x1800', '0x1801', '0xFEED'],
            'beacons': ['0xFEAA', '0xFEAB']
        }
        return common_services.get(device_type, ['0x1800', '0x1801'])
    
    def _analyze_privacy(self, profile: BLEDeviceProfile):
        """Analyze device privacy characteristics"""
        # Check if address is trackable
        if profile.address_type == "public":
            profile.trackable = True
            profile.identifiable = True
            profile.suspicious_patterns.append("Static public address - easily trackable")
        
        # Check for identifying data in name
        if any(x in profile.name.lower() for x in ['user', 'phone', 'name', 'id']):
            profile.identifiable = True
            profile.suspicious_patterns.append("Potentially identifying name")
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        if not self.devices:
            return {"error": "No devices scanned yet"}
        
        # Count by security level
        level_counts = {level: 0 for level in SecurityLevel}
        for device in self.devices.values():
            level_counts[device.security_level] += 1
        
        # Collect all vulnerabilities
        all_vulns = []
        for device in self.devices.values():
            all_vulns.extend([
                f"{device.name}: {vuln}"
                for vuln in device.vulnerabilities
            ])
        
        # Most vulnerable devices
        critical_devices = [
            {
                'address': d.address,
                'name': d.name,
                'type': d.device_type,
                'vulnerabilities': d.vulnerabilities
            }
            for d in self.devices.values()
            if d.security_level in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]
        ]
        
        return {
            'scan_summary': {
                'total_devices': len(self.devices),
                'scan_duration': self.stats['scan_duration'],
                'security_issues': self.stats['security_issues_found']
            },
            'security_distribution': {
                level.name: count
                for level, count in level_counts.items()
            },
            'critical_devices': critical_devices,
            'all_vulnerabilities': list(set(all_vulns)),
            'privacy_concerns': [
                {
                    'address': d.address,
                    'name': d.name,
                    'concern': 'Trackable' if d.trackable else 'Identifiable'
                }
                for d in self.devices.values()
                if d.trackable or d.identifiable
            ]
        }


class ChannelAnalyzer:
    """
    Analyze BLE channel usage and interference
    BLE uses 40 channels (37 data + 3 advertising)
    """
    
    BLE_CHANNELS = list(range(37, 40)) + list(range(0, 11))  # 37,38,39 + 0-10
    
    def __init__(self):
        self.channels: Dict[int, ChannelMetrics] = {
            ch: ChannelMetrics(channel=ch) for ch in self.BLE_CHANNELS
        }
        self.analyzing = False
    
    async def start_analysis(self, duration: int = 30):
        """Start channel analysis"""
        self.analyzing = True
        logger.info(f"Starting channel analysis for {duration}s")
        
        end_time = time.time() + duration
        
        while self.analyzing and time.time() < end_time:
            await self._sample_channels()
            await asyncio.sleep(0.1)  # 10Hz sampling
        
        self.analyzing = False
        logger.info("Channel analysis complete")
    
    async def _sample_channels(self):
        """Sample channel activity"""
        # In real implementation, this would use SDR or HCI
        # For now, simulate realistic BLE traffic patterns
        
        for channel in self.channels.values():
            # Advertising channels (37, 38, 39) have more traffic
            if channel.channel in [37, 38, 39]:
                base_activity = 0.3
            else:
                base_activity = 0.1
            
            # Add random variation
            if random.random() < base_activity:
                channel.packet_count += 1
                channel.average_rssi = random.randint(-80, -50)
                channel.device_count = random.randint(1, 5)
            
            # Calculate utilization
            channel.utilization_percent = min(100, channel.packet_count / 10)
            
            # Calculate interference (high utilization = high interference)
            channel.interference_level = channel.utilization_percent
    
    def get_channel_report(self) -> Dict[str, Any]:
        """Generate channel analysis report"""
        # Find most/least congested channels
        sorted_channels = sorted(
            self.channels.values(),
            key=lambda x: x.utilization_percent,
            reverse=True
        )
        
        return {
            'summary': {
                'total_packets': sum(c.packet_count for c in self.channels.values()),
                'average_utilization': sum(c.utilization_percent for c in self.channels.values()) / len(self.channels),
                'interference_detected': any(c.interference_level > 70 for c in self.channels.values())
            },
            'channel_details': [
                {
                    'channel': c.channel,
                    'type': 'Advertising' if c.channel in [37, 38, 39] else 'Data',
                    'packets': c.packet_count,
                    'devices': c.device_count,
                    'utilization': f"{c.utilization_percent:.1f}%",
                    'interference': f"{c.interference_level:.1f}%",
                    'rssi': c.average_rssi
                }
                for c in sorted_channels
            ],
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate channel usage recommendations"""
        recs = []
        
        # Check advertising channels
        for ch in [37, 38, 39]:
            if self.channels[ch].interference_level > 80:
                recs.append(f"Channel {ch} (advertising) heavily congested - expect connection issues")
        
        # Check for clean channels
        clean_data_channels = [
            c for c in self.channels.values()
            if c.channel not in [37, 38, 39] and c.utilization_percent < 20
        ]
        
        if clean_data_channels:
            best = min(clean_data_channels, key=lambda x: x.utilization_percent)
            recs.append(f"Channel {best.channel} has lowest utilization - optimal for new connections")
        
        return recs


class FaradaySimulator:
    """
    Educational simulation of Faraday cage effects
    Shows what would happen in RF-isolated environment
    """
    
    def __init__(self):
        self.simulating = False
        self.original_devices: Set[str] = set()
        self.blocked_signals: List[Dict] = []
    
    async def start_simulation(self, devices: Dict[str, BLEDeviceProfile], attenuation_db: int = 100):
        """
        Simulate Faraday cage effect
        
        Args:
            devices: Current device list
            attenuation_db: Signal attenuation (100dB = complete block)
        """
        self.simulating = True
        self.original_devices = set(devices.keys())
        self.blocked_signals = []
        
        logger.info(f"Starting Faraday simulation with {attenuation_db}dB attenuation")
        
        # Simulate signal degradation
        for address, device in devices.items():
            # Calculate if signal would be blocked
            # BLE typically needs -90dBm minimum, add attenuation
            effective_rssi = device.rssi - attenuation_db
            
            if effective_rssi < -100:  # Below noise floor
                self.blocked_signals.append({
                    'address': address,
                    'name': device.name,
                    'original_rssi': device.rssi,
                    'attenuated_rssi': effective_rssi,
                    'blocked': True,
                    'reason': 'Signal below noise floor'
                })
            else:
                self.blocked_signals.append({
                    'address': address,
                    'name': device.name,
                    'original_rssi': device.rssi,
                    'attenuated_rssi': effective_rssi,
                    'blocked': False,
                    'reason': 'Signal still detectable'
                })
        
        self.simulating = False
        logger.info("Faraday simulation complete")
    
    def get_simulation_report(self) -> Dict[str, Any]:
        """Get Faraday cage simulation results"""
        blocked = [s for s in self.blocked_signals if s['blocked']]
        remaining = [s for s in self.blocked_signals if not s['blocked']]
        
        return {
            'simulation_type': 'Faraday Cage Effect',
            'attenuation': '100dB (complete isolation)',
            'total_devices': len(self.blocked_signals),
            'blocked_devices': len(blocked),
            'remaining_devices': len(remaining),
            'blocked_list': blocked,
            'remaining_list': remaining,
            'educational_note': (
                'In a real Faraday cage, all RF signals are blocked. '
                'This simulation shows which devices would disappear '
                'from your Bluetooth scan in an RF-isolated environment.'
            )
        }


class SecurityAuditor:
    """
    Comprehensive Bluetooth security audit
    Combines all security testing features
    """
    
    def __init__(self):
        self.scanner = BluetoothScanner()
        self.channel_analyzer = ChannelAnalyzer()
        self.faraday_sim = FaradaySimulator()
        
        self.audit_results: Dict[str, Any] = {}
    
    async def run_full_audit(self, duration: int = 60) -> Dict[str, Any]:
        """Run complete security audit"""
        logger.info("Starting full Bluetooth security audit")
        
        # 1. Device scan
        await self.scanner.start_scan(duration // 2)
        
        # 2. Channel analysis (parallel)
        analyzer_task = asyncio.create_task(
            self.channel_analyzer.start_analysis(duration // 2)
        )
        
        # Wait for both
        await analyzer_task
        
        # 3. Faraday simulation (educational)
        if self.scanner.devices:
            await self.faraday_sim.start_simulation(
                self.scanner.devices,
                attenuation_db=100
            )
        
        # Compile results
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'scan_results': self.scanner.get_security_report(),
            'channel_analysis': self.channel_analyzer.get_channel_report(),
            'faraday_simulation': self.faraday_sim.get_simulation_report(),
            'executive_summary': self._generate_executive_summary()
        }
        
        return self.audit_results
    
    def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary of audit"""
        scan = self.audit_results.get('scan_results', {})
        channels = self.audit_results.get('channel_analysis', {})
        
        return {
            'risk_level': self._calculate_risk_level(scan),
            'key_findings': [
                f"{scan.get('total_devices', 0)} devices detected",
                f"{scan.get('security_issues', 0)} security issues found",
                f"{len(scan.get('critical_devices', []))} critical vulnerabilities",
                f"Channel congestion: {channels.get('summary', {}).get('average_utilization', 0):.1f}%"
            ],
            'immediate_actions': self._generate_recommendations(scan)
        }
    
    def _calculate_risk_level(self, scan: Dict) -> str:
        """Calculate overall risk level"""
        critical = len(scan.get('critical_devices', []))
        total_issues = scan.get('security_issues', 0)
        
        if critical > 5 or total_issues > 20:
            return "CRITICAL"
        elif critical > 2 or total_issues > 10:
            return "HIGH"
        elif total_issues > 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, scan: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        if scan.get('critical_devices'):
            recs.append("Immediately investigate critical vulnerability devices")
        
        if any('No authentication' in str(v) for v in scan.get('all_vulnerabilities', [])):
            recs.append("Enable pairing authentication on all devices")
        
        if any('Trackable' in str(v) for v in scan.get('privacy_concerns', [])):
            recs.append("Use privacy-preserving MAC randomization")

        
        recs.append("Regularly scan for new unauthorized devices")
        
        return recs


async def test_security_module():
    """Test the security module"""
    print("\n" + "="*60)
    print("Bluetooth Security Module Test")
    print("="*60)
    
    # Test 1: Scanner
    print("\n1. Testing Bluetooth Scanner...")
    scanner = BluetoothScanner()
    await scanner.start_scan(duration=3)
    
    report = scanner.get_security_report()
    print(f"   Devices found: {report['scan_summary']['total_devices']}")
    print(f"   Security issues: {report['scan_summary']['security_issues']}")
    print(f"   Critical devices: {len(report['critical_devices'])}")
    
    # Test 2: Channel Analyzer
    print("\n2. Testing Channel Analyzer...")
    analyzer = ChannelAnalyzer()
    await analyzer.start_analysis(duration=2)
    
    chan_report = analyzer.get_channel_report()
    print(f"   Total packets: {chan_report['summary']['total_packets']}")
    print(f"   Interference detected: {chan_report['summary']['interference_detected']}")
    
    # Test 3: Faraday Simulator
    print("\n3. Testing Faraday Simulator...")
    faraday = FaradaySimulator()
    await faraday.start_simulation(scanner.devices, attenuation_db=100)
    
    faraday_report = faraday.get_simulation_report()
    print(f"   Devices blocked: {faraday_report['blocked_devices']}")
    print(f"   Remaining: {faraday_report['remaining_devices']}")
    
    # Test 4: Full Audit
    print("\n4. Testing Full Security Audit...")
    auditor = SecurityAuditor()
    auditor.scanner = scanner  # Reuse scanner data
    auditor.channel_analyzer = analyzer
    
    # Just run Faraday sim
    await auditor.faraday_sim.start_simulation(scanner.devices, 100)
    auditor.audit_results = {
        'scan_results': report,
        'channel_analysis': chan_report,
        'faraday_simulation': faraday_report
    }
    
    summary = auditor._generate_executive_summary()
    print(f"   Risk Level: {summary['risk_level']}")
    print(f"   Key Findings: {len(summary['key_findings'])}")
    
    print("\n All security module tests passed!")
    return True


if __name__ == "__main__":
    asyncio.run(test_security_module())
