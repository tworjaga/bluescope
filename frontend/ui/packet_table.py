"""
Packet Table - Display captured Bluetooth packets
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class PacketTable(QWidget):
    """Table widget for displaying Bluetooth packets"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Filter bar
        filter_layout = QHBoxLayout()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(" Search packets...")
        self.search_box.textChanged.connect(self.filter_packets)
        filter_layout.addWidget(self.search_box)
        
        self.protocol_filter = QComboBox()
        self.protocol_filter.addItems(["All Protocols", "ATT", "L2CAP", "HCI", "SMP", "GATT"])
        self.protocol_filter.currentTextChanged.connect(self.filter_packets)
        filter_layout.addWidget(self.protocol_filter)
        
        clear_btn = QPushButton(" Clear")
        clear_btn.clicked.connect(self.clear_packets)
        filter_layout.addWidget(clear_btn)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "No.", "Time", "Source", "Destination", "Protocol",
            "Length", "RSSI", "Info"
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
        """Add sample packet data"""
        packets = [
            ("1", "10:35:42.123", "00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF", "ATT", "27", "-65", "Read Request"),
            ("2", "10:35:42.145", "AA:BB:CC:DD:EE:FF", "00:11:22:33:44:55", "ATT", "31", "-66", "Read Response"),
            ("3", "10:35:42.201", "11:22:33:44:55:66", "Broadcast", "ADV", "42", "-58", "Advertising"),
            ("4", "10:35:42.305", "00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF", "L2CAP", "64", "-67", "Connection Request"),
            ("5", "10:35:42.320", "AA:BB:CC:DD:EE:FF", "00:11:22:33:44:55", "L2CAP", "48", "-65", "Connection Response"),
            ("6", "10:35:42.401", "FF:EE:DD:CC:BB:AA", "00:11:22:33:44:55", "GATT", "52", "-72", "Notification"),
            ("7", "10:35:42.502", "00:11:22:33:44:55", "FF:EE:DD:CC:BB:AA", "GATT", "28", "-70", "Write Request"),
            ("8", "10:35:42.601", "11:22:33:44:55:66", "Broadcast", "ADV", "38", "-60", "Scan Response"),
            ("9", "10:35:42.705", "12:34:56:78:90:AB", "00:11:22:33:44:55", "SMP", "45", "-80", "Pairing Request"),
            ("10", "10:35:42.801", "00:11:22:33:44:55", "12:34:56:78:90:AB", "SMP", "47", "-78", "Pairing Response"),
        ]
        
        self.table.setRowCount(len(packets))
        
        for row, packet in enumerate(packets):
            for col, value in enumerate(packet):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Color code by protocol
                if col == 4:  # Protocol column
                    if value == "ATT":
                        item.setForeground(QColor("#007bff"))
                    elif value == "L2CAP":
                        item.setForeground(QColor("#28a745"))
                    elif value == "GATT":
                        item.setForeground(QColor("#17a2b8"))
                    elif value == "SMP":
                        item.setForeground(QColor("#ffc107"))
                    elif value == "ADV":
                        item.setForeground(QColor("#6f42c1"))
                
                # Color code RSSI
                if col == 6:  # RSSI column
                    rssi = int(value)
                    if rssi > -60:
                        item.setForeground(QColor("#28a745"))
                    elif rssi > -75:
                        item.setForeground(QColor("#ffc107"))
                    else:
                        item.setForeground(QColor("#dc3545"))
                
                self.table.setItem(row, col, item)
    
    def filter_packets(self):
        """Filter packets by search text and protocol"""
        search_text = self.search_box.text().lower()
        protocol = self.protocol_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Check search text
            if search_text:
                match = False
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        match = True
                        break
                if not match:
                    show_row = False
            
            # Check protocol filter
            if protocol != "All Protocols":
                protocol_item = self.table.item(row, 4)
                if protocol_item and protocol_item.text() != protocol:
                    show_row = False
            
            self.table.setRowHidden(row, not show_row)
    
    def clear_packets(self):
        """Clear all packets"""
        self.table.setRowCount(0)
    
    def update_packets(self, packets_data):
        """Update table with real packet data from capture manager"""
        self.table.setRowCount(len(packets_data))
        
        for row, packet in enumerate(packets_data):
            # Packet number
            item = QTableWidgetItem(str(row + 1))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item)
            
            # Time
            item = QTableWidgetItem(packet.get('timestamp', '--:--:--'))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item)
            
            # Source
            item = QTableWidgetItem(packet.get('address', 'Unknown'))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item)
            
            # Destination (determine from packet type)
            dest = "Broadcast" if packet.get('type') in ['ADV_IND', 'ADV_NONCONN_IND', 'SCAN_RSP'] else "Central"
            item = QTableWidgetItem(dest)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, item)
            
            # Protocol (determine from packet type)
            protocol = self._determine_protocol(packet.get('type', 'ADV'))
            item = QTableWidgetItem(protocol)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Color code by protocol
            if protocol == "ATT":
                item.setForeground(QColor("#007bff"))
            elif protocol == "L2CAP":
                item.setForeground(QColor("#28a745"))
            elif protocol == "GATT":
                item.setForeground(QColor("#17a2b8"))
            elif protocol == "SMP":
                item.setForeground(QColor("#ffc107"))
            elif protocol == "ADV":
                item.setForeground(QColor("#6f42c1"))
            self.table.setItem(row, 4, item)
            
            # Length
            length = packet.get('length', 0)
            item = QTableWidgetItem(str(length))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, item)
            
            # RSSI
            rssi = packet.get('rssi', -70)
            item = QTableWidgetItem(str(rssi))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if rssi > -60:
                item.setForeground(QColor("#28a745"))
            elif rssi > -75:
                item.setForeground(QColor("#ffc107"))
            else:
                item.setForeground(QColor("#dc3545"))
            self.table.setItem(row, 6, item)
            
            # Info
            info = self._get_packet_info(packet)
            item = QTableWidgetItem(info)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, item)
    
    def _determine_protocol(self, packet_type):
        """Determine protocol from packet type"""
        if packet_type in ['ADV_IND', 'ADV_NONCONN_IND', 'ADV_DIRECT_IND', 'SCAN_REQ', 'SCAN_RSP']:
            return "ADV"
        elif packet_type in ['CONNECT_REQ']:
            return "L2CAP"
        elif packet_type in ['LL_DATA']:
            return "ATT"
        else:
            return "ADV"
    
    def _get_packet_info(self, packet):
        """Get human-readable info about packet"""
        packet_type = packet.get('type', 'Unknown')
        
        if packet_type == 'ADV_IND':
            return "Connectable Advertising"
        elif packet_type == 'ADV_NONCONN_IND':
            return "Non-connectable Advertising"
        elif packet_type == 'SCAN_RSP':
            return "Scan Response"
        elif packet_type == 'CONNECT_REQ':
            return "Connection Request"
        else:
            return f"Type: {packet_type}"
