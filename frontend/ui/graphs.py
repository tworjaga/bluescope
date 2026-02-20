"""
Graphs - Real-time visualization of traffic and RSSI
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from collections import deque


class TrafficGraph(QWidget):
    """Real-time traffic graph"""
    
    def __init__(self, max_points=60):
        super().__init__()
        self.max_points = max_points
        self.data_points = deque(maxlen=max_points)
        self.setMinimumHeight(150)
        
        # Initialize with zeros
        for _ in range(max_points):
            self.data_points.append(0)
    
    def add_data_point(self, value):
        """Add new data point"""
        self.data_points.append(value)
        self.update()
    
    def paintEvent(self, event):
        """Paint the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        
        # Title
        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 20, " Traffic (packets/sec)")
        
        # Graph area
        margin = 40
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        if len(self.data_points) < 2:
            return
        
        # Find max value for scaling
        max_value = max(self.data_points) if max(self.data_points) > 0 else 1
        
        # Draw grid lines
        painter.setPen(QPen(QColor("#333333"), 1))
        for i in range(5):
            y = margin + (height * i // 4)
            painter.drawLine(margin, y, self.width() - margin, y)
        
        # Draw graph line
        painter.setPen(QPen(QColor("#007bff"), 2))
        
        points = list(self.data_points)
        for i in range(len(points) - 1):
            x1 = margin + (width * i // (len(points) - 1))
            y1 = margin + height - int((points[i] / max_value) * height)
            x2 = margin + (width * (i + 1) // (len(points) - 1))
            y2 = margin + height - int((points[i + 1] / max_value) * height)
            painter.drawLine(x1, y1, x2, y2)
        
        # Draw current value
        painter.setPen(QColor("#ffffff"))
        font.setPointSize(12)
        painter.setFont(font)
        current_value = points[-1] if points else 0
        painter.drawText(self.width() - 100, 20, f"{current_value:.1f}")


class RSSIGraph(QWidget):
    """Real-time RSSI graph"""
    
    def __init__(self, max_points=60):
        super().__init__()
        self.max_points = max_points
        self.data_points = deque(maxlen=max_points)
        self.setMinimumHeight(150)
        
        # Initialize with -70 dBm
        for _ in range(max_points):
            self.data_points.append(-70)
    
    def add_data_point(self, value):
        """Add new data point"""
        self.data_points.append(value)
        self.update()
    
    def paintEvent(self, event):
        """Paint the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        
        # Title
        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 20, " RSSI (dBm)")
        
        # Graph area
        margin = 40
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        if len(self.data_points) < 2:
            return
        
        # RSSI range: -100 to -40 dBm
        min_rssi = -100
        max_rssi = -40
        
        # Draw grid lines
        painter.setPen(QPen(QColor("#333333"), 1))
        for i in range(5):
            y = margin + (height * i // 4)
            painter.drawLine(margin, y, self.width() - margin, y)
            # Draw RSSI labels
            rssi_value = max_rssi - ((max_rssi - min_rssi) * i // 4)
            painter.drawText(5, y + 5, f"{rssi_value}")
        
        # Draw graph line with color gradient
        points = list(self.data_points)
        for i in range(len(points) - 1):
            x1 = margin + (width * i // (len(points) - 1))
            y1 = margin + int(((max_rssi - points[i]) / (max_rssi - min_rssi)) * height)
            x2 = margin + (width * (i + 1) // (len(points) - 1))
            y2 = margin + int(((max_rssi - points[i + 1]) / (max_rssi - min_rssi)) * height)
            
            # Color based on RSSI strength
            if points[i] > -60:
                color = QColor("#28a745")  # Good
            elif points[i] > -75:
                color = QColor("#ffc107")  # Fair
            else:
                color = QColor("#dc3545")  # Poor
            
            painter.setPen(QPen(color, 2))
            painter.drawLine(x1, y1, x2, y2)
        
        # Draw current value
        painter.setPen(QColor("#ffffff"))
        font.setPointSize(12)
        painter.setFont(font)
        current_value = points[-1] if points else -70
        painter.drawText(self.width() - 100, 20, f"{current_value:.0f} dBm")
