"""
Session Replay - Replay captured sessions with timeline control
Provides playback, pause, seek, and speed control for session analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QSpinBox, QCheckBox,
    QSplitter, QWidget, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from backend.capture_manager import BLEDevice, BLEPacket
from backend.session_manager import SessionData

logger = logging.getLogger(__name__)


class ReplayThread(QThread):
    """Background thread for session replay"""
    
    packet_ready = pyqtSignal(object, float)  # packet, timestamp
    progress_update = pyqtSignal(int)  # percentage
    replay_finished = pyqtSignal()
    
    def __init__(self, packets: List[BLEPacket], speed: float = 1.0):
        super().__init__()
        self.packets = packets
        self.speed = speed
        self.is_running = False
        self.is_paused = False
        self.current_index = 0
        self.start_time = None
    
    def run(self):
        """Run replay"""
        self.is_running = True
        self.start_time = datetime.now()
        
        if not self.packets:
            self.replay_finished.emit()
            return
        
        first_packet_time = self.packets[0].timestamp
        
        while self.is_running and self.current_index < len(self.packets):
            if self.is_paused:
                self.msleep(100)
                continue
            
            packet = self.packets[self.current_index]
            
            # Calculate delay based on packet timestamp
            if self.current_index > 0:
                prev_packet = self.packets[self.current_index - 1]
                time_diff = (packet.timestamp - prev_packet.timestamp).total_seconds()
                delay_ms = int(time_diff * 1000 / self.speed)
                delay_ms = max(1, min(delay_ms, 5000))  # Clamp between 1ms and 5s
                
                self.msleep(delay_ms)
            
            # Emit packet
            relative_time = (packet.timestamp - first_packet_time).total_seconds()
            self.packet_ready.emit(packet, relative_time)
            
            # Update progress
            progress = int((self.current_index / len(self.packets)) * 100)
            self.progress_update.emit(progress)
            
            self.current_index += 1
        
        self.is_running = False
        self.replay_finished.emit()
    
    def pause(self):
        """Pause replay"""
        self.is_paused = True
    
    def resume(self):
        """Resume replay"""
        self.is_paused = False
    
    def stop(self):
        """Stop replay"""
        self.is_running = False
    
    def seek(self, index: int):
        """Seek to specific packet index"""
        self.current_index = max(0, min(index, len(self.packets) - 1))


class SessionReplayDialog(QDialog):
    """
    Session replay dialog with timeline control
    """
    
    def __init__(self, session_data: SessionData, parent=None):
        super().__init__(parent)
        
        self.session_data = session_data
        self.packets: List[BLEPacket] = []
        self.replay_thread: Optional[ReplayThread] = None
        
        self.setWindowTitle(f"Session Replay - {session_data.metadata.name}")
        self.setGeometry(100, 100, 1000, 700)
        
        self._load_session_data()
        self.init_ui()
        
        logger.info(f"SessionReplay opened: {session_data.metadata.name}")
    
    def _load_session_data(self):
        """Load packets from session data"""
        for packet_dict in self.session_data.packets:
            packet = BLEPacket(
                timestamp=datetime.fromisoformat(packet_dict['timestamp']),
                device_address=packet_dict['device_address'],
                packet_type=packet_dict['packet_type'],
                channel=packet_dict['channel'],
                rssi=packet_dict['rssi'],
                data=bytes.fromhex(packet_dict['data']),
                metadata=packet_dict.get('metadata', {})
            )
            self.packets.append(packet)
        
        logger.info(f"Loaded {len(self.packets)} packets for replay")
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(f"Session Replay: {self.session_data.metadata.name}")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Session info
        info_label = QLabel(
            f"Devices: {self.session_data.metadata.total_devices} | "
            f"Packets: {self.session_data.metadata.total_packets} | "
            f"Duration: {self.session_data.metadata.capture_duration:.1f}s"
        )
        header_layout.addWidget(info_label)
        
        layout.addLayout(header_layout)
        
        # Control panel
        control_group = QGroupBox("Playback Controls")
        control_layout = QHBoxLayout(control_group)
        
        # Play/Pause button
        self.play_btn = QPushButton(" Play")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                padding: 8px 16px;
                font-size: 12px;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        control_layout.addWidget(self.play_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_replay)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addSpacing(20)
        
        # Speed control
        control_layout.addWidget(QLabel("Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "2.0x", "5.0x", "10.0x"])
        self.speed_combo.setCurrentIndex(1)
        self.speed_combo.currentTextChanged.connect(self.change_speed)
        control_layout.addWidget(self.speed_combo)
        
        control_layout.addSpacing(20)
        
        # Progress
        control_layout.addWidget(QLabel("Progress:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        control_layout.addWidget(self.progress_bar, stretch=1)
        
        layout.addWidget(control_group)
        
        # Timeline slider
        timeline_layout = QHBoxLayout()
        timeline_layout.addWidget(QLabel("Timeline:"))
        
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, max(len(self.packets) - 1, 0))
        self.timeline_slider.setValue(0)
        self.timeline_slider.valueChanged.connect(self.seek_to_packet)
        timeline_layout.addWidget(self.timeline_slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        timeline_layout.addWidget(self.time_label)
        
        layout.addLayout(timeline_layout)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Packet list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("Packet Timeline"))
        
        self.packet_table = QTableWidget()
        self.packet_table.setColumnCount(5)
        self.packet_table.setHorizontalHeaderLabels([
            "Time", "Type", "Address", "Channel", "RSSI"
        ])
        self.packet_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.packet_table.setMaximumWidth(400)
        
        left_layout.addWidget(self.packet_table)
        
        splitter.addWidget(left_widget)
        
        # Right: Packet details and visualization
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Current packet info
        self.current_packet_group = QGroupBox("Current Packet")
        current_layout = QFormLayout(self.current_packet_group)
        
        self.current_time = QLabel("--:--:--")
        self.current_type = QLabel("-")
        self.current_address = QLabel("-")
        self.current_channel = QLabel("-")
        self.current_rssi = QLabel("-")
        self.current_data = QTextEdit()
        self.current_data.setReadOnly(True)
        self.current_data.setMaximumHeight(100)
        
        current_layout.addRow("Time:", self.current_time)
        current_layout.addRow("Type:", self.current_type)
        current_layout.addRow("Address:", self.current_address)
        current_layout.addRow("Channel:", self.current_channel)
        current_layout.addRow("RSSI:", self.current_rssi)
        current_layout.addRow("Data:", self.current_data)
        
        right_layout.addWidget(self.current_packet_group)
        
        # Statistics during replay
        self.stats_group = QGroupBox("Replay Statistics")
        stats_layout = QFormLayout(self.stats_group)
        
        self.stats_packets_played = QLabel("0")
        self.stats_devices_seen = QLabel("0")
        self.stats_current_speed = QLabel("1.0x")
        self.stats_elapsed_time = QLabel("00:00")
        
        stats_layout.addRow("Packets Played:", self.stats_packets_played)
        stats_layout.addRow("Devices Seen:", self.stats_devices_seen)
        stats_layout.addRow("Current Speed:", self.stats_current_speed)
        stats_layout.addRow("Elapsed Time:", self.stats_elapsed_time)
        
        right_layout.addWidget(self.stats_group)
        
        # Event log
        right_layout.addWidget(QLabel("Event Log"))
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumHeight(150)
        right_layout.addWidget(self.event_log)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export Replay")
        self.export_btn.clicked.connect(self.export_replay)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close_dialog)
        
        btn_layout.addWidget(self.export_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # Populate packet table
        self._populate_packet_table()
    
    def _populate_packet_table(self):
        """Populate packet timeline table"""
        self.packet_table.setRowCount(min(len(self.packets), 1000))  # Limit to 1000 for performance
        
        for i, packet in enumerate(self.packets[:1000]):
            self.packet_table.setItem(i, 0, QTableWidgetItem(str(packet.timestamp.strftime("%H:%M:%S.%f")[:-3])))
            self.packet_table.setItem(i, 1, QTableWidgetItem(packet.packet_type))
            self.packet_table.setItem(i, 2, QTableWidgetItem(packet.device_address))
            self.packet_table.setItem(i, 3, QTableWidgetItem(str(packet.channel)))
            self.packet_table.setItem(i, 4, QTableWidgetItem(f"{packet.rssi} dBm"))
    
    def toggle_playback(self):
        """Toggle play/pause"""
        if self.replay_thread is None:
            self.start_replay()
        elif self.replay_thread.is_paused:
            self.resume_replay()
        else:
            self.pause_replay()
    
    def start_replay(self):
        """Start replay"""
        speed_text = self.speed_combo.currentText()
        speed = float(speed_text.replace('x', ''))
        
        self.replay_thread = ReplayThread(self.packets, speed)
        self.replay_thread.packet_ready.connect(self.on_packet_ready)
        self.replay_thread.progress_update.connect(self.on_progress_update)
        self.replay_thread.replay_finished.connect(self.on_replay_finished)
        
        self.replay_thread.start()
        
        self.play_btn.setText("⏸ Pause")
        self.log_event("Replay started")
        
        logger.info(f"Replay started at {speed}x speed")
    
    def pause_replay(self):
        """Pause replay"""
        if self.replay_thread:
            self.replay_thread.pause()
            self.play_btn.setText(" Resume")
            self.log_event("Replay paused")
    
    def resume_replay(self):
        """Resume replay"""
        if self.replay_thread:
            self.replay_thread.resume()
            self.play_btn.setText("⏸ Pause")
            self.log_event("Replay resumed")
    
    def stop_replay(self):
        """Stop replay"""
        if self.replay_thread:
            self.replay_thread.stop()
            self.replay_thread.wait()
            self.replay_thread = None
        
        self.play_btn.setText(" Play")
        self.progress_bar.setValue(0)
        self.timeline_slider.setValue(0)
        self.log_event("Replay stopped")
    
    def seek_to_packet(self, index: int):
        """Seek to specific packet"""
        if self.replay_thread:
            self.replay_thread.seek(index)
        
        # Update display
        if 0 <= index < len(self.packets):
            packet = self.packets[index]
            self.update_current_packet(packet, 0)
    
    def change_speed(self, speed_text: str):
        """Change playback speed"""
        speed = float(speed_text.replace('x', ''))
        
        if self.replay_thread:
            self.replay_thread.speed = speed
        
        self.stats_current_speed.setText(f"{speed}x")
        self.log_event(f"Speed changed to {speed}x")
    
    def on_packet_ready(self, packet: BLEPacket, relative_time: float):
        """Handle packet from replay thread"""
        self.update_current_packet(packet, relative_time)
        
        # Update timeline
        if self.replay_thread:
            self.timeline_slider.setValue(self.replay_thread.current_index)
        
        # Update stats
        self.stats_packets_played.setText(str(self.replay_thread.current_index if self.replay_thread else 0))
        
        # Format time
        minutes = int(relative_time // 60)
        seconds = int(relative_time % 60)
        self.stats_elapsed_time.setText(f"{minutes:02d}:{seconds:02d}")
    
    def on_progress_update(self, progress: int):
        """Handle progress update"""
        self.progress_bar.setValue(progress)
    
    def on_replay_finished(self):
        """Handle replay completion"""
        self.play_btn.setText(" Play")
        self.log_event("Replay finished")
        logger.info("Replay finished")
    
    def update_current_packet(self, packet: BLEPacket, relative_time: float):
        """Update current packet display"""
        self.current_time.setText(str(packet.timestamp))
        self.current_type.setText(packet.packet_type)
        self.current_address.setText(packet.device_address)
        self.current_channel.setText(str(packet.channel))
        self.current_rssi.setText(f"{packet.rssi} dBm")
        self.current_data.setText(f"Hex: {packet.data.hex()[:64]}...")
        
        # Highlight in table
        if self.replay_thread:
            self.packet_table.selectRow(self.replay_thread.current_index)
    
    def log_event(self, message: str):
        """Add event to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.event_log.append(f"[{timestamp}] {message}")
    
    def export_replay(self):
        """Export replay as video or data"""
        self.log_event("Export functionality would be implemented here")
    
    def close_dialog(self):
        """Close dialog"""
        self.stop_replay()
        self.accept()
    
    def closeEvent(self, event):
        """Handle close event"""
        self.stop_replay()
        event.accept()


# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from backend.session_manager import SessionMetadata, SessionData
    from datetime import datetime
    
    app = QApplication(sys.argv)
    
    # Create test session data
    metadata = SessionMetadata(
        session_id="test_session_001",
        name="Test Replay Session",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        description="Test session for replay functionality",
        total_packets=100,
        total_devices=5,
        capture_duration=60.0
    )
    
    # Create test packets
    packets = []
    for i in range(100):
        packet = {
            'timestamp': (datetime.now() + __import__('datetime').timedelta(milliseconds=i*100)).isoformat(),
            'device_address': f"AA:BB:CC:DD:EE:{i%5:02d}",
            'packet_type': ['ADV_IND', 'SCAN_RSP', 'CONNECT_REQ'][i % 3],
            'channel': 37 + (i % 3),
            'rssi': -65 - (i % 20),
            'data': '0201060303AAFE',
            'metadata': {}
        }
        packets.append(packet)
    
    session_data = SessionData(
        metadata=metadata,
        devices=[],
        packets=packets,
        statistics={},
        settings={}
    )
    
    # Test dialog
    dialog = SessionReplayDialog(session_data)
    dialog.exec()
    
    sys.exit(0)

