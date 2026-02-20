""" Live Capture View - Real-time signal visualization and duplication control """

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LiveSignalTable(QTableWidget):
    """Table for displaying live captured signals"""
    
    def __init__(self, max_rows=100):
        super().__init__()
        self.max_rows = max_rows
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Time", "Device", "Type", "Channel", "RSSI", "Status"
        ])
        self.setMaximumHeight(200)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #333333;
            }
        """)
    
    def add_signal(self, timestamp: str, device: str, signal_type: str,
                   channel: int, rssi: int, status: str = "Captured"):
        """Add a signal to the table"""
        row = self.rowCount()
        if row >= self.max_rows:
            self.removeRow(0)
            row = self.max_rows - 1
        
        self.insertRow(row)
        
        # Time
        self.setItem(row, 0, QTableWidgetItem(timestamp))
        
        # Device
        self.setItem(row, 1, QTableWidgetItem(device))
        
        # Type
        self.setItem(row, 2, QTableWidgetItem(signal_type))
        
        # Channel
        self.setItem(row, 3, QTableWidgetItem(str(channel)))
        
        # RSSI
        rssi_item = QTableWidgetItem(f"{rssi} dBm")
        if rssi > -60:
            rssi_item.setForeground(QColor("#28a745"))
        elif rssi > -75:
            rssi_item.setForeground(QColor("#ffc107"))
        else:
            rssi_item.setForeground(QColor("#dc3545"))
        self.setItem(row, 4, rssi_item)
        
        # Status
        status_item = QTableWidgetItem(status)
        if status == "Duplicated":
            status_item.setForeground(QColor("#17a2b8"))
        elif status == "Replayed":
            status_item.setForeground(QColor("#6f42c1"))
        self.setItem(row, 5, status_item)
        
        self.scrollToBottom()


class LiveCaptureView(QWidget):
    """Live capture view with signal duplication controls"""
    
    duplication_started = pyqtSignal()
    duplication_stopped = pyqtSignal()
    replay_started = pyqtSignal()
    replay_stopped = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duplicator = None
        self.init_ui()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)
        
        logger.info("LiveCaptureView initialized")
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel(" LIVE SIGNAL CAPTURE & DUPLICATION")
        title.setStyleSheet("""
            QLabel {
                color: #dc3545;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # Right panel
        right_panel = self.create_live_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #252526;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #333333;
            }
        """)
        layout.addWidget(self.status_label)
    
    def create_control_panel(self):
        """Create control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Recording
        record_group = QGroupBox(" Recording")
        record_layout = QVBoxLayout(record_group)
        
        self.record_btn = QPushButton("⏺ Start Recording")
        self.record_btn.setCheckable(True)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #dc3545;
            }
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.clicked.connect(self.toggle_recording)
        
        self.recorded_count = QLabel("Recorded: 0 signals")
        record_layout.addWidget(self.recorded_count)
        
        buttons = QHBoxLayout()
        clear_btn = QPushButton(" Clear")
        clear_btn.clicked.connect(self.clear_recorded)
        buttons.addWidget(clear_btn)
        
        export_btn = QPushButton(" Export")
        export_btn.clicked.connect(self.export_signals)
        buttons.addWidget(export_btn)
        
        import_btn = QPushButton(" Import")
        import_btn.clicked.connect(self.import_signals)
        buttons.addWidget(import_btn)
        record_layout.addLayout(buttons)
        
        layout.addWidget(record_group)
        
        # Duplication
        dup_group = QGroupBox(" Live Duplication")
        dup_layout = QVBoxLayout(dup_group)
        
        self.dup_enabled = QCheckBox("Enable Live Duplication")
        self.dup_enabled.setStyleSheet("color: #17a2b8; font-weight: bold;")
        dup_layout.addWidget(self.dup_enabled)
        
        # Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.dup_mode = QComboBox()
        self.dup_mode.addItems(["Immediate", "Delayed", "Burst", "Random Interval"])
        mode_layout.addWidget(self.dup_mode)
        dup_layout.addLayout(mode_layout)
        
        # Delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay (ms):"))
        self.dup_delay = QSpinBox()
        self.dup_delay.setRange(0, 10000)
        self.dup_delay.setValue(100)
        self.dup_delay.setSuffix(" ms")
        delay_layout.addWidget(self.dup_delay)
        dup_layout.addLayout(delay_layout)
        
        # Burst
        burst_layout = QHBoxLayout()
        burst_layout.addWidget(QLabel("Burst Count:"))
        self.burst_count = QSpinBox()
        self.burst_count.setRange(1, 100)
        self.burst_count.setValue(1)
        burst_layout.addWidget(self.burst_count)
        dup_layout.addLayout(burst_layout)
        
        # Max replays
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max Replays:"))
        self.max_replays = QSpinBox()
        self.max_replays.setRange(0, 1000)
        self.max_replays.setValue(0)
        self.max_replays.setSpecialValueText("Unlimited")
        max_layout.addWidget(self.max_replays)
        dup_layout.addLayout(max_layout)
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_device = QComboBox()
        self.filter_device.addItem("All Devices")
        self.filter_device.setEditable(True)
        filter_layout.addWidget(self.filter_device)
        dup_layout.addLayout(filter_layout)
        
        # Start button
        self.dup_btn = QPushButton(" Start Duplication")
        self.dup_btn.setCheckable(True)
        self.dup_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #dc3545;
            }
        """)
        self.dup_btn.clicked.connect(self.toggle_duplication)
        dup_layout.addWidget(self.dup_btn)
        
        self.dup_count = QLabel("Duplicated: 0 signals")
        dup_layout.addWidget(self.dup_count)
        
        layout.addWidget(dup_group)
        
        # Replay
        replay_group = QGroupBox(" Replay")
        replay_layout = QVBoxLayout(replay_group)
        
        self.replay_btn = QPushButton(" Start Replay")
        self.replay_btn.setCheckable(True)
        self.replay_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #dc3545;
            }
        """)
        self.replay_btn.clicked.connect(self.toggle_replay)
        replay_layout.addWidget(self.replay_btn)
        
        self.replay_count = QLabel("Replayed: 0 signals")
        replay_layout.addWidget(self.replay_count)
        
        layout.addWidget(replay_group)
        layout.addStretch()
        
        return panel
    
    def create_live_panel(self):
        """Create live view panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Signal table
        self.signal_table = LiveSignalTable(max_rows=100)
        layout.addWidget(self.signal_table)
        
        # Statistics
        stats_group = QGroupBox(" Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        self.stats_recorded = QLabel("Recorded: 0")
        self.stats_duplicated = QLabel("Duplicated: 0")
        self.stats_replayed = QLabel("Replayed: 0")
        self.stats_dropped = QLabel("Dropped: 0")
        
        stats_layout.addWidget(self.stats_recorded)
        stats_layout.addWidget(self.stats_duplicated)
        stats_layout.addWidget(self.stats_replayed)
        stats_layout.addWidget(self.stats_dropped)
        
        layout.addWidget(stats_group)
        
        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.log_output)
        
        return panel
    
    def set_duplicator(self, duplicator):
        """Set duplicator instance"""
        self.duplicator = duplicator
        if duplicator:
            duplicator.on_signal_recorded = self._on_signal_recorded
            duplicator.on_signal_duplicated = self._on_signal_duplicated
            duplicator.on_signal_replayed = self._on_signal_replayed
    
    def _on_signal_recorded(self, record):
        """Handle recorded signal"""
        timestamp = record.timestamp.strftime("%H:%M:%S.%f")[:-3]
        device = record.metadata.get('local_name', record.device_address[:8])
        self.signal_table.add_signal(timestamp, device, record.signal_type,
                                      record.channel, record.rssi, "Recorded")
        self.log(f" Recorded: {device} - {record.signal_type}")
    
    def _on_signal_duplicated(self, record):
        """Handle duplicated signal"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        device = record.metadata.get('local_name', record.device_address[:8])
        self.signal_table.add_signal(timestamp, device, record.signal_type,
                                      record.channel, record.rssi, "Duplicated")
        self.log(f" Duplicated: {device}")
    
    def _on_signal_replayed(self, record):
        """Handle replayed signal"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        device = record.metadata.get('local_name', record.device_address[:8])
        self.signal_table.add_signal(timestamp, device, record.signal_type,
                                      record.channel, record.rssi, "Replayed")
        self.log(f" Replayed: {device}")
    
    def log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def toggle_recording(self):
        """Toggle recording"""
        if not self.duplicator:
            self.log(" Duplicator not initialized")
            self.record_btn.setChecked(False)
            return
        
        if self.record_btn.isChecked():
            self.duplicator.start_recording()
            self.record_btn.setText("⏹ Stop Recording")
            self.status_label.setText(" Recording...")
            self.log(" Recording started")
        else:
            self.duplicator.stop_recording()
            self.record_btn.setText("⏺ Start Recording")
            self.status_label.setText("Recording stopped")
            self.log("⏹ Recording stopped")
    
    def toggle_duplication(self):
        """Toggle duplication"""
        if not self.duplicator:
            self.log(" Duplicator not initialized")
            self.dup_btn.setChecked(False)
            return
        
        if self.dup_btn.isChecked():
            from backend.signal_duplicator import DuplicationConfig
            
            mode_map = {0: "immediate", 1: "delayed", 2: "burst", 3: "random"}
            
            config = DuplicationConfig(
                enabled=self.dup_enabled.isChecked(),
                replay_mode=mode_map.get(self.dup_mode.currentIndex(), "immediate"),
                delay_ms=self.dup_delay.value(),
                burst_count=self.burst_count.value(),
                max_replays=self.max_replays.value(),
                filter_device=None if self.filter_device.currentText() == "All Devices" 
                              else self.filter_device.currentText()
            )
            
            self.duplicator.config = config
            self.duplicator.start_duplication()
            self.dup_btn.setText("⏹ Stop Duplication")
            self.status_label.setText(" Live duplication active")
            self.log(" Live duplication started")
            self.duplication_started.emit()
        else:
            self.duplicator.stop_duplication()
            self.dup_btn.setText(" Start Duplication")
            self.status_label.setText("Duplication stopped")
            self.log("⏹ Live duplication stopped")
            self.duplication_stopped.emit()
    
    def toggle_replay(self):
        """Toggle replay"""
        if not self.duplicator:
            self.log(" Duplicator not initialized")
            self.replay_btn.setChecked(False)
            return
        
        if self.replay_btn.isChecked():
            self.duplicator.start_replay()
            self.replay_btn.setText("⏹ Stop Replay")
            self.status_label.setText(" Replaying...")
            self.log(" Replay started")
            self.replay_started.emit()
        else:
            self.duplicator.stop_replay()
            self.replay_btn.setText(" Start Replay")
            self.status_label.setText("Replay stopped")
            self.log("⏹ Replay stopped")
            self.replay_stopped.emit()
    
    def clear_recorded(self):
        """Clear recorded signals"""
        if self.duplicator:
            self.duplicator.clear_recorded()
            self.log(" Cleared")
            self.signal_table.setRowCount(0)
    
    def export_signals(self):
        """Export signals"""
        if not self.duplicator:
            return
        
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getSaveFileName(self, "Export", "signals.json",
                                                  "JSON Files (*.json)")
        if filepath:
            self.duplicator.export_recorded(filepath)
            self.log(f" Exported to {filepath}")
    
    def import_signals(self):
        """Import signals"""
        if not self.duplicator:
            return
        
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(self, "Import", "",
                                                  "JSON Files (*.json)")
        if filepath:
            self.duplicator.import_recorded(filepath)
            self.log(f" Imported from {filepath}")
    
    def update_stats(self):
        """Update statistics"""
        if not self.duplicator:
            return
        
        stats = self.duplicator.get_statistics()
        self.recorded_count.setText(f"Recorded: {stats['recorded']} signals")
        self.dup_count.setText(f"Duplicated: {stats['duplicated']} signals")
        self.replay_count.setText(f"Replayed: {stats['replayed']} signals")
        self.stats_recorded.setText(f"Recorded: {stats['recorded']}")
        self.stats_duplicated.setText(f"Duplicated: {stats['duplicated']}")
        self.stats_replayed.setText(f"Replayed: {stats['replayed']}")
        self.stats_dropped.setText(f"Dropped: {stats['dropped']}")
    
    def closeEvent(self, event):
        """Handle close"""
        if self.duplicator:
            self.duplicator.stop_recording()
            self.duplicator.stop_duplication()
            self.duplicator.stop_replay()
        event.accept()
