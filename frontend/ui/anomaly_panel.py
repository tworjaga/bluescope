"""
Anomaly Panel - Display detected anomalies
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QComboBox, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class AnomalyPanel(QWidget):
    """Panel for displaying detected anomalies"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Filter bar
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Severity:"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.severity_filter.currentTextChanged.connect(self.filter_anomalies)
        filter_layout.addWidget(self.severity_filter)
        
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Behavioral", "Statistical", "ML-Based"])
        self.type_filter.currentTextChanged.connect(self.filter_anomalies)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addStretch()
        
        clear_btn = QPushButton(" Clear All")
        clear_btn.clicked.connect(self.clear_anomalies)
        filter_layout.addWidget(clear_btn)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Time", "Device", "Type", "Severity", "Score",
            "Description", "Action"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # Add sample data
        self.add_sample_data()
    
    def add_sample_data(self):
        """Add sample anomaly data"""
        anomalies = [
            ("10:35:42", "00:11:22:33:44:55", "Behavioral", "High", "0.85",
             "Unusual connection pattern detected", "Investigate"),
            ("10:34:15", "AA:BB:CC:DD:EE:FF", "Statistical", "Medium", "0.62",
             "Packet rate deviation: 150% above baseline", "Review"),
            ("10:32:08", "11:22:33:44:55:66", "ML-Based", "Critical", "0.92",
             "Isolation Forest detected outlier behavior", "Alert"),
            ("10:30:45", "FF:EE:DD:CC:BB:AA", "Behavioral", "Low", "0.35",
             "Minor temporal pattern deviation", "Monitor"),
            ("10:28:22", "12:34:56:78:90:AB", "Statistical", "High", "0.78",
             "RSSI anomaly: Unexpected signal strength", "Investigate"),
        ]
        
        self.table.setRowCount(len(anomalies))
        
        for row, anomaly in enumerate(anomalies):
            for col, value in enumerate(anomaly):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Color code by severity
                if col == 3:  # Severity column
                    if value == "Critical":
                        item.setForeground(QColor("#dc3545"))
                        item.setBackground(QColor("#dc354520"))
                    elif value == "High":
                        item.setForeground(QColor("#fd7e14"))
                        item.setBackground(QColor("#fd7e1420"))
                    elif value == "Medium":
                        item.setForeground(QColor("#ffc107"))
                        item.setBackground(QColor("#ffc10720"))
                    else:
                        item.setForeground(QColor("#28a745"))
                        item.setBackground(QColor("#28a74520"))
                
                # Color code score
                if col == 4:  # Score column
                    score = float(value)
                    if score >= 0.8:
                        item.setForeground(QColor("#dc3545"))
                    elif score >= 0.6:
                        item.setForeground(QColor("#ffc107"))
                    else:
                        item.setForeground(QColor("#28a745"))
                
                # Color code type
                if col == 2:  # Type column
                    if value == "ML-Based":
                        item.setForeground(QColor("#6f42c1"))
                    elif value == "Behavioral":
                        item.setForeground(QColor("#007bff"))
                    else:
                        item.setForeground(QColor("#17a2b8"))
                
                self.table.setItem(row, col, item)
    
    def filter_anomalies(self):
        """Filter anomalies by severity and type"""
        severity = self.severity_filter.currentText()
        anomaly_type = self.type_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Check severity filter
            if severity != "All":
                severity_item = self.table.item(row, 3)
                if severity_item and severity_item.text() != severity:
                    show_row = False
            
            # Check type filter
            if anomaly_type != "All":
                type_item = self.table.item(row, 2)
                if type_item and type_item.text() != anomaly_type:
                    show_row = False
            
            self.table.setRowHidden(row, not show_row)
    
    def clear_anomalies(self):
        """Clear all anomalies"""
        self.table.setRowCount(0)
    
    def get_anomaly_count(self):
        """Get total number of anomalies"""
        return self.table.rowCount()
    
    def update_anomalies(self, anomalies_data):
        """Update table with real anomaly data"""
        current_count = self.table.rowCount()
        self.table.setRowCount(current_count + len(anomalies_data))
        
        for i, anomaly in enumerate(anomalies_data):
            row = current_count + i
            
            # Time
            item = QTableWidgetItem(anomaly.get('time', '--:--:--'))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item)
            
            # Device
            item = QTableWidgetItem(anomaly.get('device', 'Unknown'))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item)
            
            # Type
            anomaly_type = anomaly.get('type', 'Statistical')
            item = QTableWidgetItem(anomaly_type)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if anomaly_type == "ML-Based":
                item.setForeground(QColor("#6f42c1"))
            elif anomaly_type == "Behavioral":
                item.setForeground(QColor("#007bff"))
            else:
                item.setForeground(QColor("#17a2b8"))
            self.table.setItem(row, 2, item)
            
            # Severity
            severity = anomaly.get('severity', 'Low')
            item = QTableWidgetItem(severity)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if severity == "Critical":
                item.setForeground(QColor("#dc3545"))
                item.setBackground(QColor("#dc354520"))
            elif severity == "High":
                item.setForeground(QColor("#fd7e14"))
                item.setBackground(QColor("#fd7e1420"))
            elif severity == "Medium":
                item.setForeground(QColor("#ffc107"))
                item.setBackground(QColor("#ffc10720"))
            else:
                item.setForeground(QColor("#28a745"))
                item.setBackground(QColor("#28a74520"))
            self.table.setItem(row, 3, item)
            
            # Score
            score = anomaly.get('score', 0.0)
            item = QTableWidgetItem(f"{score:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if score >= 0.8:
                item.setForeground(QColor("#dc3545"))
            elif score >= 0.6:
                item.setForeground(QColor("#ffc107"))
            else:
                item.setForeground(QColor("#28a745"))
            self.table.setItem(row, 4, item)
            
            # Description
            item = QTableWidgetItem(anomaly.get('description', 'No description'))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, item)
            
            # Action
            item = QTableWidgetItem(anomaly.get('action', 'Monitor'))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, item)
    
    def add_anomaly(self, time, device, anomaly_type, severity, score, description, action):
        """Add a single anomaly to the table"""
        row = self.table.rowCount()
        self.table.setRowCount(row + 1)
        
        # Time
        item = QTableWidgetItem(time)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, item)
        
        # Device
        item = QTableWidgetItem(device)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, item)
        
        # Type
        item = QTableWidgetItem(anomaly_type)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if anomaly_type == "ML-Based":
            item.setForeground(QColor("#6f42c1"))
        elif anomaly_type == "Behavioral":
            item.setForeground(QColor("#007bff"))
        else:
            item.setForeground(QColor("#17a2b8"))
        self.table.setItem(row, 2, item)
        
        # Severity
        item = QTableWidgetItem(severity)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if severity == "Critical":
            item.setForeground(QColor("#dc3545"))
            item.setBackground(QColor("#dc354520"))
        elif severity == "High":
            item.setForeground(QColor("#fd7e14"))
            item.setBackground(QColor("#fd7e1420"))
        elif severity == "Medium":
            item.setForeground(QColor("#ffc107"))
            item.setBackground(QColor("#ffc10720"))
        else:
            item.setForeground(QColor("#28a745"))
            item.setBackground(QColor("#28a74520"))
        self.table.setItem(row, 3, item)
        
        # Score
        item = QTableWidgetItem(f"{score:.2f}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if score >= 0.8:
            item.setForeground(QColor("#dc3545"))
        elif score >= 0.6:
            item.setForeground(QColor("#ffc107"))
        else:
            item.setForeground(QColor("#28a745"))
        self.table.setItem(row, 4, item)
        
        # Description
        item = QTableWidgetItem(description)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 5, item)
        
        # Action
        item = QTableWidgetItem(action)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 6, item)
