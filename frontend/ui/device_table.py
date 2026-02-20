"""
Device Table - Display discovered Bluetooth devices
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class DeviceTable(QWidget):
    """Table widget for displaying Bluetooth devices"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(" Search devices...")
        self.search_box.textChanged.connect(self.filter_devices)
        search_layout.addWidget(self.search_box)
        
        refresh_btn = QPushButton(" Refresh")
        refresh_btn.clicked.connect(self.refresh)
        search_layout.addWidget(refresh_btn)
        
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "MAC Address", "Name", "Type", "RSSI", "First Seen",
            "Last Seen", "Packets", "Status"
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
        """Add sample device data"""
        devices = [
            ("00:11:22:33:44:55", "iPhone 13", "Phone", "-65 dBm", "10:30:15", "10:35:42", "1,234", "Active"),
            ("AA:BB:CC:DD:EE:FF", "Galaxy Watch", "Wearable", "-72 dBm", "10:28:03", "10:35:40", "856", "Active"),
            ("11:22:33:44:55:66", "AirPods Pro", "Audio", "-58 dBm", "10:32:20", "10:35:41", "2,103", "Active"),
            ("FF:EE:DD:CC:BB:AA", "Smart Band", "Fitness", "-80 dBm", "10:25:10", "10:34:15", "432", "Idle"),
            ("12:34:56:78:90:AB", "Unknown", "Unknown", "-85 dBm", "10:20:05", "10:30:22", "89", "Inactive"),
        ]
        
        self.table.setRowCount(len(devices))
        
        for row, device in enumerate(devices):
            for col, value in enumerate(device):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Color code by status
                if col == 7:  # Status column
                    if value == "Active":
                        item.setForeground(QColor("#28a745"))
                    elif value == "Idle":
                        item.setForeground(QColor("#ffc107"))
                    else:
                        item.setForeground(QColor("#6c757d"))
                
                # Color code RSSI
                if col == 3:  # RSSI column
                    rssi = int(value.split()[0])
                    if rssi > -60:
                        item.setForeground(QColor("#28a745"))
                    elif rssi > -75:
                        item.setForeground(QColor("#ffc107"))
                    else:
                        item.setForeground(QColor("#dc3545"))
                
                self.table.setItem(row, col, item)
    
    def filter_devices(self, text):
        """Filter devices by search text"""
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
    
    def refresh(self):
        """Refresh device list"""
        self.add_sample_data()
    
    def update_devices(self, devices_data):
        """Update table with real device data from capture manager"""
        # Block signals during update to prevent flickering
        self.table.setUpdatesEnabled(False)
        
        # Clear and set new row count
        self.table.clearContents()
        self.table.setRowCount(0)
        
        if not devices_data:
            self.table.setUpdatesEnabled(True)
            return
        
        self.table.setRowCount(len(devices_data))
        
        for row, device in enumerate(devices_data):
            # Handle both dict and BLEDevice objects
            if hasattr(device, 'address'):
                # It's a BLEDevice object
                address = device.address
                name = device.name or "Unknown"
                rssi = device.rssi
                packets = device.packet_count
                first_seen = device.first_seen.strftime('%H:%M:%S') if hasattr(device.first_seen, 'strftime') else str(device.first_seen)
                last_seen = device.last_seen.strftime('%H:%M:%S') if hasattr(device.last_seen, 'strftime') else str(device.last_seen)
            else:
                # It's a dict
                address = device.get('address', 'Unknown')
                name = device.get('name', '') or "Unknown"
                rssi = device.get('rssi', -70)
                packets = device.get('packets', 0)
                first_seen = device.get('first_seen', '--:--:--')
                last_seen = device.get('last_seen', '--:--:--')
            
            # MAC Address
            item = QTableWidgetItem(str(address))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item)
            
            # Name
            item = QTableWidgetItem(str(name))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item)
            
            # Type
            device_type = self._determine_device_type(str(name))
            item = QTableWidgetItem(device_type)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item)
            
            # RSSI - handle both int and string
            try:
                rssi_val = int(rssi) if isinstance(rssi, (int, float)) else int(str(rssi).split()[0])
            except (ValueError, IndexError):
                rssi_val = -70
            
            item = QTableWidgetItem(f"{rssi_val} dBm")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if rssi_val > -60:
                item.setForeground(QColor("#28a745"))
            elif rssi_val > -75:
                item.setForeground(QColor("#ffc107"))
            else:
                item.setForeground(QColor("#dc3545"))
            self.table.setItem(row, 3, item)
            
            # First Seen
            item = QTableWidgetItem(str(first_seen))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, item)
            
            # Last Seen
            item = QTableWidgetItem(str(last_seen))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, item)
            
            # Packets
            try:
                pkt_count = int(packets) if isinstance(packets, (int, float)) else int(str(packets).replace(',', ''))
            except (ValueError, AttributeError):
                pkt_count = 0
            
            item = QTableWidgetItem(f"{pkt_count:,}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, item)
            
            # Status
            status = "Active" if pkt_count > 10 else "Idle"
            item = QTableWidgetItem(status)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status == "Active":
                item.setForeground(QColor("#28a745"))
            elif status == "Idle":
                item.setForeground(QColor("#ffc107"))
            else:
                item.setForeground(QColor("#6c757d"))
            self.table.setItem(row, 7, item)
        
        # Re-enable updates and force refresh
        self.table.setUpdatesEnabled(True)
        self.table.viewport().update()
        self.table.repaint()

    
    def _determine_device_type(self, name):
        """Determine device type from name"""
        name_lower = name.lower()
        if 'iphone' in name_lower or 'samsung' in name_lower or 'pixel' in name_lower or 'xiaomi' in name_lower:
            return "Phone"
        elif 'watch' in name_lower or 'fitbit' in name_lower or 'band' in name_lower:
            return "Wearable"
        elif 'airpods' in name_lower or 'buds' in name_lower or 'headphone' in name_lower:
            return "Audio"
        elif 'tv' in name_lower or 'display' in name_lower:
            return "Display"
        elif 'keyboard' in name_lower or 'mouse' in name_lower:
            return "Input"
        elif name == "Unknown" or not name:
            return "Unknown"
        else:
            return "Other"
