"""
Main Window - BlueScope GUI
Similar to FlowScope design with Bluetooth-specific features
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QStatusBar, QMenuBar, QMenu, QToolBar,
    QPushButton, QLabel, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon
import asyncio
import logging
import threading
from pathlib import Path


from .device_table import DeviceTable
from .packet_table import PacketTable
from .statistics_panel import StatisticsPanel
from .graphs import TrafficGraph, RSSIGraph
from .anomaly_panel import AnomalyPanel
from .live_capture_view import LiveCaptureView
from ..themes.dark_theme import apply_dark_theme
from backend.export_manager import get_export_manager
from backend.bluetooth_spam import BluetoothSpammer, SpamMode, SpamConfig
from backend.signal_duplicator import get_signal_duplicator, SignalDuplicator


# Linux real transmission (only works on Linux with root)
try:
    from backend.linux_bluetooth_tx import LinuxBluetoothTransmitter, BLESpamAttack
    LINUX_TX_AVAILABLE = True
except ImportError:
    LINUX_TX_AVAILABLE = False

from backend.capture_manager import CaptureManager, BLEDevice, BLEPacket



logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    capture_started = pyqtSignal()
    capture_stopped = pyqtSignal()
    
    def __init__(self, config_path: str = None):
        super().__init__()
        
        self.config_path = config_path
        self.is_capturing = False
        
        # Initialize capture manager
        self.capture_manager = CaptureManager({'backend': 'mock'})  # Use 'bleak' for real capture
        
        # Set up capture callbacks
        self.capture_manager.on_device_discovered = self._on_device_discovered
        self.capture_manager.on_packet_received = self._on_packet_received
        
        # Initialize signal duplicator
        self.signal_duplicator = get_signal_duplicator()
        
        # Initialize export manager
        self.export_manager = get_export_manager()


        
        # Initialize UI
        self.init_ui()
        
        # Apply dark theme
        apply_dark_theme(self)
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        # Start capture thread
        self.capture_thread = None
        
        logger.info("Main window initialized")

    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("BlueScope")
        self.setGeometry(100, 100, 1600, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Tabs
        self.tabs = QTabWidget()
        self.create_tabs()
        splitter.addWidget(self.tabs)
        
        # Bottom section: Statistics and graphs
        bottom_widget = self.create_bottom_panel()
        splitter.addWidget(bottom_widget)
        
        # Set splitter sizes (60% top, 40% bottom)
        splitter.setSizes([540, 360])
        
        main_layout.addWidget(splitter)
        
        # Create status bar
        self.create_status_bar()
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Session", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_session)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Session", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_session)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("&Export to CSV", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Capture menu
        capture_menu = menubar.addMenu("&Capture")
        
        start_action = QAction("&Start Capture", self)
        start_action.setShortcut("Ctrl+P")
        start_action.triggered.connect(self.toggle_capture)
        capture_menu.addAction(start_action)
        
        stop_action = QAction("St&op Capture", self)
        stop_action.triggered.connect(self.stop_capture)
        capture_menu.addAction(stop_action)
        
        capture_menu.addSeparator()
        
        reset_action = QAction("&Reset Statistics", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.reset_statistics)
        capture_menu.addAction(reset_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        spam_action = QAction(" Bluetooth &Spam", self)
        spam_action.setShortcut("Ctrl+Shift+S")
        spam_action.triggered.connect(self.open_spam_dialog)
        tools_menu.addAction(spam_action)
        
        security_action = QAction(" Security &Audit", self)
        security_action.setShortcut("Ctrl+Shift+A")
        security_action.triggered.connect(self.open_security_audit_dialog)
        tools_menu.addAction(security_action)
        
        tools_menu.addSeparator()
        
        # Signal Duplication
        dup_action = QAction(" Signal &Duplication", self)
        dup_action.setShortcut("Ctrl+Shift+D")
        dup_action.triggered.connect(self.open_live_capture)
        tools_menu.addAction(dup_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)



        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Start/Stop button
        self.start_btn = QPushButton(" Start Capture")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_capture)
        toolbar.addWidget(self.start_btn)
        
        toolbar.addSeparator()
        
        # Device selector
        toolbar.addWidget(QLabel("  Device:"))
        self.device_selector = QPushButton("Auto-detect")
        self.device_selector.clicked.connect(self.select_device)
        toolbar.addWidget(self.device_selector)
        
        toolbar.addSeparator()
        
        # Statistics labels
        self.packets_label = QLabel("Packets: 0")
        self.devices_label = QLabel("Devices: 0")
        self.anomalies_label = QLabel("Anomalies: 0")
        
        toolbar.addWidget(self.packets_label)
        toolbar.addWidget(QLabel("  |  "))
        toolbar.addWidget(self.devices_label)
        toolbar.addWidget(QLabel("  |  "))
        toolbar.addWidget(self.anomalies_label)
    
    def create_tabs(self):
        """Create tab widgets"""
        # Devices tab
        self.device_table = DeviceTable()
        self.tabs.addTab(self.device_table, " Devices")
        
        # Packets tab
        self.packet_table = PacketTable()
        self.tabs.addTab(self.packet_table, " Packets")
        
        # Anomalies tab
        self.anomaly_panel = AnomalyPanel()
        self.tabs.addTab(self.anomaly_panel, " Anomalies")
        
        # Live Capture tab
        self.live_capture_view = LiveCaptureView()
        self.live_capture_view.set_duplicator(self.signal_duplicator)
        self.tabs.addTab(self.live_capture_view, " Live Capture")

    
    def create_bottom_panel(self):
        """Create bottom panel with statistics and graphs"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Statistics panel
        self.stats_panel = StatisticsPanel()
        layout.addWidget(self.stats_panel, 1)
        
        # Graphs
        graphs_widget = QWidget()
        graphs_layout = QVBoxLayout(graphs_widget)
        graphs_layout.setContentsMargins(0, 0, 0, 0)
        
        self.traffic_graph = TrafficGraph()
        self.rssi_graph = RSSIGraph()
        
        graphs_layout.addWidget(self.traffic_graph)
        graphs_layout.addWidget(self.rssi_graph)
        
        layout.addWidget(graphs_widget, 2)
        
        return widget
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.status_bar.addPermanentWidget(QLabel("BlueScope v0.1.0"))
    
    def toggle_capture(self):
        """Toggle capture on/off"""
        if self.is_capturing:
            self.stop_capture()
        else:
            self.start_capture()
    
    def start_capture(self):
        """Start packet capture"""
        self.is_capturing = True
        self.start_btn.setText("⏸ Stop Capture")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.status_label.setText("Capturing...")
        self.capture_started.emit()
        
        # Start capture manager in separate thread
        self.capture_thread = CaptureThread(self.capture_manager)
        self.capture_thread.start()
        
        logger.info("Capture started")

    
    def stop_capture(self):
        """Stop packet capture"""
        self.is_capturing = False
        self.start_btn.setText(" Start Capture")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.status_label.setText("Stopped")
        self.capture_stopped.emit()
        
        # Stop capture manager
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread = None
        
        logger.info("Capture stopped")

    
    def update_display(self):
        """Update display with latest data"""
        if self.is_capturing:
            # Get real statistics from capture manager
            stats = self.capture_manager.get_statistics()
            
            packets = stats['total_packets']
            devices = stats['total_devices']
            packet_rate = stats['packets_per_second']
            
            # Calculate uptime
            uptime_seconds = stats['uptime']
            uptime_str = f"{int(uptime_seconds // 3600):02d}:{int((uptime_seconds % 3600) // 60):02d}:{int(uptime_seconds % 60):02d}"
            
            # Get anomaly count from anomaly panel
            anomalies = self.anomaly_panel.get_anomaly_count() if hasattr(self.anomaly_panel, 'get_anomaly_count') else 0
            
            # Update toolbar labels
            self.packets_label.setText(f"Packets: {packets}")
            self.devices_label.setText(f"Devices: {devices}")
            self.anomalies_label.setText(f"Anomalies: {anomalies}")
            
            # Update statistics panel
            display_stats = {
                'total_packets': packets,
                'total_devices': devices,
                'packet_rate': packet_rate,
                'data_rate': packet_rate * 0.1,  # Estimate data rate
                'anomalies': anomalies,
                'uptime': uptime_str
            }
            self.stats_panel.update_statistics(display_stats)
            
            # Update graphs with real data
            self.traffic_graph.add_data_point(packet_rate)
            
            # Get average RSSI from devices
            devices_list = self.capture_manager.get_devices()
            if devices_list:
                avg_rssi = sum(d.rssi for d in devices_list) / len(devices_list)
                self.rssi_graph.add_data_point(avg_rssi)
            
            # Update tables with real data every 2 seconds
            if not hasattr(self, 'update_counter'):
                self.update_counter = 0
            self.update_counter += 1
            
            if self.update_counter % 2 == 0:  # Update tables every 2 seconds
                # Update device table with real devices
                devices_data = []
                for device in devices_list:
                    devices_data.append({
                        'address': device.address,
                        'name': device.name,
                        'rssi': device.rssi,
                        'packets': device.packet_count,
                        'first_seen': device.first_seen.strftime('%H:%M:%S'),
                        'last_seen': device.last_seen.strftime('%H:%M:%S')
                    })
                self.device_table.update_devices(devices_data)
                
                # Update packet table with real packets
                packets_list = self.capture_manager.get_packets(limit=100)
                packets_data = []
                for packet in packets_list:
                    packets_data.append({
                        'timestamp': packet.timestamp.strftime('%H:%M:%S.%f')[:-3],
                        'address': packet.device_address,
                        'type': packet.packet_type,
                        'channel': packet.channel,
                        'rssi': packet.rssi,
                        'length': len(packet.data)
                    })
                self.packet_table.update_packets(packets_data)
        else:
            # Reset counter when not capturing
            if hasattr(self, 'update_counter'):
                self.update_counter = 0
    
    def _on_device_discovered(self, device: BLEDevice):
        """Callback when new device is discovered"""
        logger.debug(f"Device discovered: {device.name} ({device.address})")
    
    def _on_packet_received(self, packet: BLEPacket):
        """Callback when packet is received"""
        logger.debug(f"Packet received from {packet.device_address}")
        
        # Record signal for duplication
        if self.signal_duplicator and self.signal_duplicator.is_recording:
            self.signal_duplicator.record_signal(
                device_address=packet.device_address,
                signal_type=packet.packet_type,
                rssi=packet.rssi,
                channel=packet.channel,
                data=packet.data,
                metadata=packet.metadata
            )


    
    def select_device(self):
        """Select capture device"""
        logger.info("Device selection requested")
    
    def open_session(self):
        """Open saved session"""
        logger.info("Open session requested")
    
    def save_session(self):
        """Save current session"""
        logger.info("Save session requested")
    
    def export_csv(self):
        """Export data to CSV"""
        logger.info("Export CSV requested")
        
        try:
            # Get current devices and packets
            devices = self.capture_manager.get_devices()
            packets = self.capture_manager.get_packets(limit=10000)
            
            # Convert to dictionaries for export
            devices_data = []
            for device in devices:
                devices_data.append({
                    'address': device.address,
                    'name': device.name,
                    'rssi': device.rssi,
                    'packet_count': device.packet_count,
                    'first_seen': device.first_seen.isoformat(),
                    'last_seen': device.last_seen.isoformat(),
                    'manufacturer_data': str(device.manufacturer_data),
                    'service_uuids': ','.join(device.service_uuids),
                    'tx_power': device.tx_power
                })
            
            packets_data = []
            for packet in packets:
                packets_data.append({
                    'timestamp': packet.timestamp.isoformat(),
                    'device_address': packet.device_address,
                    'packet_type': packet.packet_type,
                    'channel': packet.channel,
                    'rssi': packet.rssi,
                    'length': len(packet.data),
                    'data': packet.data.hex() if packet.data else ''
                })
            
            # Export devices
            if devices_data:
                devices_file = self.export_manager.export_devices_csv(devices_data)
                logger.info(f"Exported devices to: {devices_file}")
            
            # Export packets
            if packets_data:
                packets_file = self.export_manager.export_packets_csv(packets_data)
                logger.info(f"Exported packets to: {packets_file}")
            
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported:\n"
                f"- {len(devices_data)} devices\n"
                f"- {len(packets_data)} packets\n\n"
                f"Files saved to: {self.export_manager.export_dir}"
            )
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data:\n{str(e)}"
            )

    
    def reset_statistics(self):
        """Reset all statistics"""
        logger.info("Reset statistics requested")
    
    def refresh_view(self):
        """Refresh view"""
        logger.info("Refresh view requested")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def open_settings(self):
        """Open settings dialog"""
        logger.info("Settings requested")
    
    def open_live_capture(self):
        """Open live capture view (switch to Live Capture tab)"""
        # Find and switch to Live Capture tab
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == " Live Capture":
                self.tabs.setCurrentIndex(i)
                break
        logger.info("Live capture view opened")

    
    def open_spam_dialog(self):
        """Open Bluetooth spam dialog"""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
            QComboBox, QSpinBox, QPushButton, QGroupBox,
            QMessageBox, QLineEdit, QCheckBox
        )
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Bluetooth Spam - Security Testing")
        dialog.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Warning label
        warning = QLabel(" WARNING: For authorized security testing only!")
        warning.setStyleSheet("color: #dc3545; font-weight: bold;")
        layout.addWidget(warning)
        
        # Real transmission option (Linux only)
        import sys
        import os
        real_tx_checkbox = QCheckBox(" REAL TRANSMISSION (Linux root only)")
        # Enable checkbox on all platforms, but warn if not Linux
        real_tx_checkbox.setEnabled(True)
        real_tx_checkbox.setToolTip("Linux with root required for real transmission. Other platforms will show simulation only.")
        layout.addWidget(real_tx_checkbox)
        
        # Platform warning label (shown when not on Linux)
        platform_warning = QLabel("")
        platform_warning.setStyleSheet("color: #ffc107; font-size: 11px;")
        layout.addWidget(platform_warning)

        
        # Mode selection

        mode_group = QGroupBox("Spam Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        mode_combo = QComboBox()
        mode_combo.addItems([
            "Advertising Spam",
            "Connection Request Spam", 
            "L2CAP Packet Spam",
            "ATT/GATT Request Spam",
            "Random Packet Spam"
        ])
        mode_layout.addWidget(mode_combo)
        layout.addWidget(mode_group)
        
        # Rate configuration
        rate_group = QGroupBox("Packet Rate")
        rate_layout = QHBoxLayout(rate_group)
        
        rate_spin = QSpinBox()
        rate_spin.setRange(1, 1000)
        rate_spin.setValue(10)
        rate_spin.setSuffix(" pps")
        rate_layout.addWidget(rate_spin)
        layout.addWidget(rate_group)
        
        # Duration configuration
        duration_group = QGroupBox("Duration")
        duration_layout = QHBoxLayout(duration_group)
        
        duration_spin = QSpinBox()
        duration_spin.setRange(0, 3600)
        duration_spin.setValue(10)
        duration_spin.setSuffix(" sec (0 = infinite)")
        duration_layout.addWidget(duration_spin)
        layout.addWidget(duration_group)
        
        # Target address (optional)
        target_group = QGroupBox("Target Address (optional)")
        target_layout = QVBoxLayout(target_group)
        
        target_edit = QLineEdit()
        target_edit.setPlaceholderText("AA:BB:CC:DD:EE:FF")
        target_layout.addWidget(target_edit)
        layout.addWidget(target_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        start_btn = QPushButton(" Start Spam")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
        """)
        
        stop_btn = QPushButton("⏹ Stop")
        stop_btn.setEnabled(False)
        
        close_btn = QPushButton("Close")
        
        button_layout.addWidget(start_btn)
        button_layout.addWidget(stop_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        # Status label
        status_label = QLabel("Ready")
        layout.addWidget(status_label)
        
        # Spam manager
        spammer = None
        spam_thread = None
        linux_tx = None
        
        def start_spam():
            nonlocal spammer, spam_thread, linux_tx
            
            # Check if real transmission mode requested
            if real_tx_checkbox.isChecked():
                # Check platform compatibility
                if sys.platform != 'linux':
                    platform_warning.setText(" Windows: Real transmission unavailable. Using simulation.")
                    logger.warning("Real transmission requested on non-Linux platform, using simulation")
                elif os.geteuid() != 0:
                    platform_warning.setText(" Linux: Root privileges required. Using simulation.")
                    logger.warning("Real transmission requested without root, using simulation")
                elif not LINUX_TX_AVAILABLE:
                    platform_warning.setText(" Linux TX module not available. Using simulation.")
                    logger.warning("Linux TX module not available, using simulation")
                else:
                    platform_warning.setText("")
                
                # Only use real TX if all conditions met
                use_real_tx = (
                    LINUX_TX_AVAILABLE and 
                    sys.platform == 'linux' and 
                    os.geteuid() == 0
                )
                
                if use_real_tx:
                    # Real Linux transmission
                    start_btn.setEnabled(False)
                    stop_btn.setEnabled(True)
                    status_label.setText(" REAL TRANSMISSION ACTIVE - Phones will react!")
                    
                    def run_linux_spam():
                        nonlocal linux_tx
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        linux_tx = LinuxBluetoothTransmitter()
                        
                        async def spam():
                            if await linux_tx.initialize():
                                packets = BLESpamAttack.get_all_attack_packets()
                                await linux_tx.spam_advertisements(
                                    packets, 
                                    interval=1.0 / rate_spin.value()
                                )
                        
                        try:
                            loop.run_until_complete(spam())
                        except Exception as e:
                            logger.error(f"Linux spam error: {e}")
                        finally:
                            if linux_tx:
                                linux_tx.close()
                    
                    spam_thread = threading.Thread(target=run_linux_spam, daemon=True)
                    spam_thread.start()
                    
                    logger.info("Started REAL Bluetooth spam via Linux HCI")
                    return
                
                # Simulation mode (default or fallback)

                mode_map = {
                    0: SpamMode.ADVERTISING,
                    1: SpamMode.CONNECTION,
                    2: SpamMode.L2CAP,
                    3: SpamMode.ATT,
                    4: SpamMode.RANDOM
                }
                mode = mode_map.get(mode_combo.currentIndex(), SpamMode.ADVERTISING)
                
                config = SpamConfig(
                    mode=mode,
                    packet_rate=rate_spin.value(),
                    duration=duration_spin.value(),
                    target_address=target_edit.text() if target_edit.text() else None
                )
                
                spammer = BluetoothSpammer(config)
                
                def on_packet(count):
                    from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                    try:
                        QMetaObject.invokeMethod(
                            status_label, 
                            "setText",
                            Qt.ConnectionType.QueuedConnection,
                            Q_ARG(str, f"Sent {count} packets (SIMULATION)")
                        )
                    except RuntimeError:
                        # QLabel has been deleted (dialog closed)
                        pass

                
                spammer.on_packet_sent = on_packet
                
                def run_spam():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(spammer.start())
                        while spammer.is_running:
                            loop.run_until_complete(asyncio.sleep(0.1))
                    except Exception as e:
                        logger.error(f"Spam thread error: {e}")
                    finally:
                        loop.close()
                
                spam_thread = threading.Thread(target=run_spam, daemon=True)
                spam_thread.start()
                
                start_btn.setEnabled(False)
                stop_btn.setEnabled(True)
                status_label.setText("Simulation running (no real transmission)")
                
                logger.info(f"Started simulated Bluetooth spam: {mode.name}")
        
        def stop_spam():
            nonlocal spammer, spam_thread, linux_tx
            
            if linux_tx:
                linux_tx.is_transmitting = False
                linux_tx = None
            
            if spammer:
                asyncio.run_coroutine_threadsafe(spammer.stop(), asyncio.new_event_loop())
                spammer = None
            
            if spam_thread:
                spam_thread = None
            
            start_btn.setEnabled(True)
            stop_btn.setEnabled(False)
            status_label.setText("Stopped")
            
            logger.info("Stopped Bluetooth spam")


        
        start_btn.clicked.connect(start_spam)
        stop_btn.clicked.connect(stop_spam)
        close_btn.clicked.connect(dialog.accept)
        
        dialog.exec()

    def open_security_audit_dialog(self):
        """Open Bluetooth security audit dialog using fixed implementation"""
        from frontend.ui.security_dialog import SecurityAuditDialog
        
        dialog = SecurityAuditDialog(self)
        dialog.exec()
    
    def show_about(self):

        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About BlueScope",
            "BlueScope v0.1.0\n\n"
            "Enterprise Bluetooth Monitoring Platform\n\n"
            "Built with Python, Rust, and Go\n"
            "Designed for professional security analysis"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_capturing:
            self.stop_capture()
        event.accept()


class CaptureThread(QThread):
    """Thread for running capture manager"""
    
    def __init__(self, capture_manager: CaptureManager):
        super().__init__()
        self.capture_manager = capture_manager
        self._is_running = False
    
    def run(self):
        """Run capture loop"""
        self._is_running = True
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Start capture
            loop.run_until_complete(self.capture_manager.start_capture())
            
            # Keep running until stopped
            while self._is_running and self.capture_manager.is_capturing:
                loop.run_until_complete(asyncio.sleep(0.1))
                
        except Exception as e:
            logger.error(f"Capture thread error: {e}")
        finally:
            # Stop capture
            try:
                loop.run_until_complete(self.capture_manager.stop_capture())
            except:
                pass
            loop.close()
    
    def stop(self):
        """Stop capture thread"""
        self._is_running = False
        self.wait(2000)  # Wait up to 2 seconds
