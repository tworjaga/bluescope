"""
Statistics Panel - Display capture statistics
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StatCard(QFrame):
    """Individual statistic card"""
    
    def __init__(self, title, value, color="#007bff"):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(9)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(self.value_label)
    
    def update_value(self, value):
        """Update card value"""
        self.value_label.setText(value)


class StatisticsPanel(QWidget):
    """Panel displaying capture statistics"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel(" Statistics")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Stats grid
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Create stat cards
        self.total_packets = StatCard("Total Packets", "0", "#007bff")
        self.total_devices = StatCard("Devices", "0", "#28a745")
        self.packet_rate = StatCard("Packets/sec", "0", "#17a2b8")
        self.data_rate = StatCard("KB/sec", "0", "#6f42c1")
        self.anomalies = StatCard("Anomalies", "0", "#dc3545")
        self.uptime = StatCard("Uptime", "00:00:00", "#ffc107")
        
        # Add to grid
        grid.addWidget(self.total_packets, 0, 0)
        grid.addWidget(self.total_devices, 0, 1)
        grid.addWidget(self.packet_rate, 1, 0)
        grid.addWidget(self.data_rate, 1, 1)
        grid.addWidget(self.anomalies, 2, 0)
        grid.addWidget(self.uptime, 2, 1)
        
        layout.addLayout(grid)
        layout.addStretch()
    
    def update_statistics(self, stats):
        """Update statistics display"""
        self.total_packets.update_value(str(stats.get('total_packets', 0)))
        self.total_devices.update_value(str(stats.get('total_devices', 0)))
        self.packet_rate.update_value(f"{stats.get('packet_rate', 0):.1f}")
        self.data_rate.update_value(f"{stats.get('data_rate', 0):.1f}")
        self.anomalies.update_value(str(stats.get('anomalies', 0)))
        self.uptime.update_value(stats.get('uptime', '00:00:00'))
