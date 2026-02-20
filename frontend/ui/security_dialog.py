#!/usr/bin/env python3
"""
Fixed Security Audit Dialog for BlueScope
Properly handles table updates without invokeMethod issues
"""

import sys
import asyncio
import threading
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QTextEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from backend.bluetooth_security import (
    BluetoothScanner, ChannelAnalyzer, 
    FaradaySimulator, SecurityAuditor
)

logger = logging.getLogger(__name__)


class SecurityAuditDialog(QDialog):
    """Bluetooth Security Audit Dialog - Fixed Version"""
    
    # Signal to update UI from thread
    scan_complete = pyqtSignal(dict)
    channel_complete = pyqtSignal(dict)
    faraday_complete = pyqtSignal(dict)
    audit_complete = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(" Bluetooth Security Audit")
        self.setGeometry(200, 200, 1000, 800)
        
        # Connect signals
        self.scan_complete.connect(self._on_scan_complete)
        self.channel_complete.connect(self._on_channel_complete)
        self.faraday_complete.connect(self._on_faraday_complete)
        self.audit_complete.connect(self._on_audit_complete)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Warning
        warning = QLabel(" For authorized security testing only!")
        warning.setStyleSheet("color: #dc3545; font-weight: bold; font-size: 14px;")
        layout.addWidget(warning)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Device Scanner
        self._init_scan_tab()
        
        # Tab 2: Channel Analyzer
        self._init_channel_tab()
        
        # Tab 3: Faraday Simulator
        self._init_faraday_tab()
        
        # Tab 4: Full Audit
        self._init_audit_tab()
        
        layout.addWidget(self.tabs)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _init_scan_tab(self):
        """Initialize device scanner tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scan button
        self.scan_btn = QPushButton(" Start Security Scan")
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-size: 16px;
                padding: 15px;
            }
        """)
        self.scan_btn.clicked.connect(self._run_scan)
        layout.addWidget(self.scan_btn)
        
        # Results table
        self.scan_table = QTableWidget()
        self.scan_table.setColumnCount(4)
        self.scan_table.setHorizontalHeaderLabels([
            "Device", "Type", "Security Level", "Vulnerabilities"
        ])
        self.scan_table.setAlternatingRowColors(True)
        layout.addWidget(self.scan_table)
        
        # Status
        self.scan_status = QLabel("Ready to scan")
        layout.addWidget(self.scan_status)
        
        self.tabs.addTab(tab, "Device Scanner")
    
    def _init_channel_tab(self):
        """Initialize channel analyzer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Analyze button
        self.channel_btn = QPushButton(" Analyze Channels")
        self.channel_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                padding: 15px;
            }
        """)
        self.channel_btn.clicked.connect(self._run_channel_analysis)
        layout.addWidget(self.channel_btn)
        
        # Results table
        self.channel_table = QTableWidget()
        self.channel_table.setColumnCount(5)
        self.channel_table.setHorizontalHeaderLabels([
            "Channel", "Type", "Utilization", "Interference", "Devices"
        ])
        self.channel_table.setAlternatingRowColors(True)
        layout.addWidget(self.channel_table)
        
        # Status
        self.channel_status = QLabel("Channel analysis ready")
        layout.addWidget(self.channel_status)
        
        self.tabs.addTab(tab, "Channel Analyzer")
    
    def _init_faraday_tab(self):
        """Initialize Faraday simulator tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info = QLabel(
            "Faraday Cage Simulator (Educational)\n"
            "Shows what happens to Bluetooth signals in RF isolation"
        )
        info.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(info)
        
        self.faraday_btn = QPushButton(" Simulate Faraday Cage")
        self.faraday_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-size: 16px;
                padding: 15px;
            }
        """)
        self.faraday_btn.clicked.connect(self._run_faraday_sim)
        layout.addWidget(self.faraday_btn)
        
        self.faraday_results = QTextEdit()
        self.faraday_results.setReadOnly(True)
        layout.addWidget(self.faraday_results)
        
        self.tabs.addTab(tab, "Faraday Simulator")
    
    def _init_audit_tab(self):
        """Initialize full audit tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.audit_btn = QPushButton(" Run Full Security Audit")
        self.audit_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-size: 16px;
                padding: 15px;
            }
        """)
        self.audit_btn.clicked.connect(self._run_full_audit)
        layout.addWidget(self.audit_btn)
        
        self.audit_results = QTextEdit()
        self.audit_results.setReadOnly(True)
        layout.addWidget(self.audit_results)
        
        self.tabs.addTab(tab, "Full Audit")
    
    def _run_scan(self):
        """Run device security scan"""
        self.scan_btn.setEnabled(False)
        self.scan_status.setText("Scanning... (3 seconds)")
        self.scan_table.setRowCount(0)  # Clear table
        
        def do_scan():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def scan_task():
                    scanner = BluetoothScanner()
                    await scanner.start_scan(duration=3)
                    return scanner.get_security_report()
                
                report = loop.run_until_complete(scan_task())
                
                # Emit signal to update UI in main thread
                self.scan_complete.emit(report)
                
            except Exception as e:
                logger.error(f"Scan error: {e}")
                self.scan_complete.emit({'error': str(e)})
        
        threading.Thread(target=do_scan, daemon=True).start()
    
    def _on_scan_complete(self, report):
        """Handle scan completion (runs in main thread)"""
        if 'error' in report:
            self.scan_status.setText(f"Error: {report['error']}")
            self.scan_btn.setEnabled(True)
            return
        
        # Collect all devices
        all_devices = []
        
        for device in report.get('critical_devices', []):
            all_devices.append({
                'name': device['name'],
                'type': device['type'],
                'level': 'CRITICAL',
                'vulns': "; ".join(device['vulnerabilities'])
            })
        
        for concern in report.get('privacy_concerns', []):
            if not any(d['name'] == concern['name'] for d in all_devices):
                all_devices.append({
                    'name': concern['name'],
                    'type': 'Unknown',
                    'level': concern['concern'],
                    'vulns': f"Privacy: {concern['concern']}"
                })
        
        # Populate table
        self.scan_table.setRowCount(len(all_devices))
        
        for i, device in enumerate(all_devices):
            self.scan_table.setItem(i, 0, QTableWidgetItem(device['name']))
            self.scan_table.setItem(i, 1, QTableWidgetItem(device['type']))
            self.scan_table.setItem(i, 2, QTableWidgetItem(device['level']))
            self.scan_table.setItem(i, 3, QTableWidgetItem(device['vulns']))
        
        self.scan_btn.setEnabled(True)
        self.scan_status.setText(
            f"Found {len(all_devices)} devices with security issues "
            f"(Total: {report['scan_summary']['total_devices']})"
        )
    
    def _run_channel_analysis(self):
        """Run channel analysis"""
        self.channel_btn.setEnabled(False)
        self.channel_status.setText("Analyzing channels... (2 seconds)")
        self.channel_table.setRowCount(0)  # Clear table
        
        def do_analysis():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def analysis_task():
                    analyzer = ChannelAnalyzer()
                    await analyzer.start_analysis(duration=2)
                    return analyzer.get_channel_report()
                
                report = loop.run_until_complete(analysis_task())
                
                # Emit signal to update UI
                self.channel_complete.emit(report)
                
            except Exception as e:
                logger.error(f"Channel analysis error: {e}")
                self.channel_complete.emit({'error': str(e)})
        
        threading.Thread(target=do_analysis, daemon=True).start()
    
    def _on_channel_complete(self, report):
        """Handle channel analysis completion"""
        if 'error' in report:
            self.channel_status.setText(f"Error: {report['error']}")
            self.channel_btn.setEnabled(True)
            return
        
        channels = report.get('channel_details', [])
        
        # Populate table
        self.channel_table.setRowCount(len(channels))
        
        for i, ch in enumerate(channels):
            self.channel_table.setItem(i, 0, QTableWidgetItem(str(ch['channel'])))
            self.channel_table.setItem(i, 1, QTableWidgetItem(ch['type']))
            self.channel_table.setItem(i, 2, QTableWidgetItem(ch['utilization']))
            self.channel_table.setItem(i, 3, QTableWidgetItem(ch['interference']))
            self.channel_table.setItem(i, 4, QTableWidgetItem(str(ch['devices'])))
        
        self.channel_btn.setEnabled(True)
        self.channel_status.setText(
            f"Analyzed {len(channels)} channels, "
            f"{report['summary']['total_packets']} packets"
        )
    
    def _run_faraday_sim(self):
        """Run Faraday simulation"""
        self.faraday_btn.setEnabled(False)
        self.faraday_results.setText("Running Faraday simulation...")
        
        def do_sim():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def sim_task():
                    scanner = BluetoothScanner()
                    await scanner.start_scan(duration=2)
                    
                    faraday = FaradaySimulator()
                    await faraday.start_simulation(scanner.devices, attenuation_db=100)
                    
                    return faraday.get_simulation_report()
                
                report = loop.run_until_complete(sim_task())
                self.faraday_complete.emit(report)
                
            except Exception as e:
                logger.error(f"Faraday sim error: {e}")
                self.faraday_complete.emit({'error': str(e)})
        
        threading.Thread(target=do_sim, daemon=True).start()
    
    def _on_faraday_complete(self, report):
        """Handle Faraday simulation completion"""
        if 'error' in report:
            self.faraday_results.setText(f"Error: {report['error']}")
            self.faraday_btn.setEnabled(True)
            return
        
        result_text = f"""
         FARADAY CAGE SIMULATION RESULTS                  


Attenuation: {report['attenuation']}
Total Devices: {report['total_devices']}
Blocked: {report['blocked_devices']}
Remaining: {report['remaining_devices']}

EDUCATIONAL NOTE:
{report['educational_note']}

BLOCKED DEVICES:
"""
        for dev in report['blocked_list']:
            result_text += f"   {dev['name']} ({dev['address']})\n"
            result_text += f"     RSSI: {dev['original_rssi']}dBm → {dev['attenuated_rssi']}dBm\n"
        
        self.faraday_results.setText(result_text)
        self.faraday_btn.setEnabled(True)
    
    def _run_full_audit(self):
        """Run full security audit"""
        self.audit_btn.setEnabled(False)
        self.audit_results.setText("Running comprehensive security audit...\nThis may take 10-15 seconds...")
        
        def do_audit():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def audit_task():
                    auditor = SecurityAuditor()
                    return await auditor.run_full_audit(duration=10)
                
                report = loop.run_until_complete(audit_task())
                self.audit_complete.emit(report)
                
            except Exception as e:
                logger.error(f"Audit error: {e}")
                self.audit_complete.emit({'error': str(e)})
        
        threading.Thread(target=do_audit, daemon=True).start()
    
    def _on_audit_complete(self, report):
        """Handle full audit completion"""
        if 'error' in report:
            self.audit_results.setText(f"Error: {report['error']}")
            self.audit_btn.setEnabled(True)
            return
        
        summary = report['executive_summary']
        scan = report['scan_results']
        
        result_text = f"""
      BLUETOOTH SECURITY AUDIT REPORT                     


TIMESTAMP: {report['timestamp']}
OVERALL RISK LEVEL: {summary['risk_level']}


 EXECUTIVE SUMMARY                                        

"""
        for finding in summary['key_findings']:
            result_text += f"  • {finding}\n"
        
        result_text += "\n\n"
        result_text += " IMMEDIATE ACTIONS REQUIRED                               \n"
        result_text += "\n"
        for action in summary['immediate_actions']:
            result_text += f"    {action}\n"
        
        result_text += "\n\n"
        result_text += " CRITICAL DEVICES                                         \n"
        result_text += "\n"
        for device in scan.get('critical_devices', [])[:5]:
            result_text += f"\n   {device['name']} ({device['address']})\n"
            result_text += f"     Type: {device['type']}\n"
            for vuln in device['vulnerabilities']:
                result_text += f"       {vuln}\n"
        
        self.audit_results.setText(result_text)
        self.audit_btn.setEnabled(True)


# For testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = SecurityAuditDialog()
    dialog.exec()
