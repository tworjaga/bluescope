"""
Packet Inspector Dialog - Detailed packet inspection view
Provides hex dump, protocol analysis, and field breakdown
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QSplitter, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QFont
from PyQt6.QtGui import QColor, QBrush, QFont as QGuiFont
from typing import Optional, Dict, Any
import logging

from backend.capture_manager import BLEPacket
from backend.protocol_parser import get_protocol_parser, ParsedPacket

logger = logging.getLogger(__name__)


class PacketInspectorDialog(QDialog):
    """
    Detailed packet inspection dialog
    Shows hex dump, protocol layers, and field breakdown
    """
    
    def __init__(self, packet: BLEPacket, parent=None):
        super().__init__(parent)
        
        self.packet = packet
        self.parsed_packet: Optional[ParsedPacket] = None
        
        self.setWindowTitle(f"Packet Inspector - {packet.device_address}")
        self.setGeometry(100, 100, 900, 700)
        
        # Parse packet
        self._parse_packet()
        
        self.init_ui()
        self.populate_data()
        
        logger.info(f"PacketInspector opened for {packet.device_address}")
    
    def _parse_packet(self):
        """Parse the packet using protocol parser"""
        parser = get_protocol_parser()
        self.parsed_packet = parser.parse_packet(
            self.packet.data,
            timestamp=self.packet.timestamp.timestamp(),
            rssi=self.packet.rssi,
            channel=self.packet.channel
        )
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Packet Inspector")
        self.title_label.setFont(QGuiFont("Segoe UI", 14, QGuiFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        header_layout.addWidget(self.close_btn)
        
        layout.addLayout(header_layout)
        
        # Summary bar
        summary_group = QGroupBox("Packet Summary")
        summary_layout = QFormLayout(summary_group)
        
        self.summary_device = QLabel()
        self.summary_type = QLabel()
        self.summary_size = QLabel()
        self.summary_protocol = QLabel()
        
        summary_layout.addRow("Device:", self.summary_device)
        summary_layout.addRow("Type:", self.summary_type)
        summary_layout.addRow("Size:", self.summary_size)
        summary_layout.addRow("Protocol Stack:", self.summary_protocol)
        
        layout.addWidget(summary_group)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Overview tab
        self.overview_tab = self._create_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Hex Dump tab
        self.hex_tab = self._create_hex_tab()
        self.tabs.addTab(self.hex_tab, "Hex Dump")
        
        # Protocol Stack tab
        self.protocol_tab = self._create_protocol_tab()
        self.tabs.addTab(self.protocol_tab, "Protocol Stack")
        
        # Fields tab
        self.fields_tab = self._create_fields_tab()
        self.tabs.addTab(self.fields_tab, "Field Breakdown")
    
    def _create_overview_tab(self) -> QWidget:
        """Create overview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Packet info
        info_group = QGroupBox("Packet Information")
        info_layout = QFormLayout(info_group)
        
        self.info_timestamp = QLabel()
        self.info_address = QLabel()
        self.info_rssi = QLabel()
        self.info_channel = QLabel()
        self.info_type = QLabel()
        
        info_layout.addRow("Timestamp:", self.info_timestamp)
        info_layout.addRow("Device Address:", self.info_address)
        info_layout.addRow("RSSI:", self.info_rssi)
        info_layout.addRow("Channel:", self.info_channel)
        info_layout.addRow("Packet Type:", self.info_type)
        
        layout.addWidget(info_group)
        
        # Protocol analysis
        if self.parsed_packet and self.parsed_packet.protocol_stack:
            proto_group = QGroupBox("Protocol Analysis")
            proto_layout = QVBoxLayout(proto_group)
            
            for layer in self.parsed_packet.protocol_stack:
                proto_layout.addWidget(QLabel(f"• {layer}"))
            
            layout.addWidget(proto_group)
        
        # Raw data preview
        data_group = QGroupBox("Raw Data Preview (first 32 bytes)")
        data_layout = QVBoxLayout(data_group)
        
        self.data_preview = QTextEdit()
        self.data_preview.setReadOnly(True)
        self.data_preview.setMaximumHeight(100)
        self.data_preview.setFont(QGuiFont("Consolas", 10))
        
        data_layout.addWidget(self.data_preview)
        layout.addWidget(data_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_hex_tab(self) -> QWidget:
        """Create hex dump tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Hex dump display
        self.hex_display = QTextEdit()
        self.hex_display.setReadOnly(True)
        self.hex_display.setFont(QGuiFont("Consolas", 11))
        self.hex_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
        """)
        
        layout.addWidget(self.hex_display)
        
        # ASCII display
        ascii_group = QGroupBox("ASCII Representation")
        ascii_layout = QVBoxLayout(ascii_group)
        
        self.ascii_display = QTextEdit()
        self.ascii_display.setReadOnly(True)
        self.ascii_display.setMaximumHeight(150)
        self.ascii_display.setFont(QGuiFont("Consolas", 10))
        
        ascii_layout.addWidget(self.ascii_display)
        layout.addWidget(ascii_group)
        
        return tab
    
    def _create_protocol_tab(self) -> QWidget:
        """Create protocol stack tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Protocol tree
        self.protocol_tree = QTreeWidget()
        self.protocol_tree.setHeaderLabels(["Layer", "Field", "Value", "Description"])
        self.protocol_tree.setColumnWidth(0, 150)
        self.protocol_tree.setColumnWidth(1, 150)
        self.protocol_tree.setColumnWidth(2, 200)
        
        layout.addWidget(self.protocol_tree)
        
        return tab
    
    def _create_fields_tab(self) -> QWidget:
        """Create field breakdown tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Fields table
        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(4)
        self.fields_table.setHorizontalHeaderLabels([
            "Field Name", "Value", "Type", "Offset"
        ])
        self.fields_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        
        layout.addWidget(self.fields_table)
        
        return tab
    
    def populate_data(self):
        """Populate all tabs with packet data"""
        # Summary
        self.summary_device.setText(f"{self.packet.device_address}")
        self.summary_type.setText(self.packet.packet_type)
        self.summary_size.setText(f"{len(self.packet.data)} bytes")
        
        if self.parsed_packet:
            self.summary_protocol.setText(" → ".join(self.parsed_packet.protocol_stack))
        
        # Overview
        self.info_timestamp.setText(str(self.packet.timestamp))
        self.info_address.setText(self.packet.device_address)
        self.info_rssi.setText(f"{self.packet.rssi} dBm")
        self.info_channel.setText(str(self.packet.channel))
        self.info_type.setText(self.packet.packet_type)
        
        # Data preview
        preview = self.packet.data[:32]
        self.data_preview.setText(f"Hex: {preview.hex()}\nLength: {len(self.packet.data)} bytes")
        
        # Hex dump
        self._populate_hex_dump()
        
        # Protocol tree
        self._populate_protocol_tree()
        
        # Fields table
        self._populate_fields_table()
    
    def _populate_hex_dump(self):
        """Populate hex dump display"""
        data = self.packet.data
        hex_lines = []
        ascii_lines = []
        
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            
            # Hex line
            hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
            hex_line = f"{i:04X}:  {hex_bytes:<48}"
            hex_lines.append(hex_line)
            
            # ASCII line
            ascii_chars = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            ascii_lines.append(ascii_chars)
        
        self.hex_display.setText('\n'.join(hex_lines))
        self.ascii_display.setText('\n'.join(ascii_lines))
    
    def _populate_protocol_tree(self):
        """Populate protocol tree with parsed data"""
        if not self.parsed_packet:
            return
        
        # Link Layer
        ll_item = QTreeWidgetItem(self.protocol_tree)
        ll_item.setText(0, "Link Layer")
        ll_item.setText(1, "Type")
        ll_item.setText(2, self.parsed_packet.ll_type)
        
        # L2CAP
        if self.parsed_packet.l2cap_cid:
            l2cap_item = QTreeWidgetItem(self.protocol_tree)
            l2cap_item.setText(0, "L2CAP")
            l2cap_item.setText(1, "CID")
            l2cap_item.setText(2, f"0x{self.parsed_packet.l2cap_cid:04X}")
            
            l2cap_len = QTreeWidgetItem(l2cap_item)
            l2cap_len.setText(1, "Length")
            l2cap_len.setText(2, str(self.parsed_packet.l2cap_length))
        
        # ATT
        if self.parsed_packet.att_opcode:
            att_item = QTreeWidgetItem(self.protocol_tree)
            att_item.setText(0, "ATT")
            att_item.setText(1, "Opcode")
            att_item.setText(2, f"0x{self.parsed_packet.att_opcode:02X}")
            att_item.setText(3, self.parsed_packet.att_opcode_name)
            
            if self.parsed_packet.att_handle:
                att_handle = QTreeWidgetItem(att_item)
                att_handle.setText(1, "Handle")
                att_handle.setText(2, f"0x{self.parsed_packet.att_handle:04X}")
        
        # Advertising
        if self.parsed_packet.adv_local_name:
            adv_item = QTreeWidgetItem(self.protocol_tree)
            adv_item.setText(0, "Advertising")
            adv_item.setText(1, "Local Name")
            adv_item.setText(2, self.parsed_packet.adv_local_name)
        
        self.protocol_tree.expandAll()
    
    def _populate_fields_table(self):
        """Populate fields table"""
        fields = []
        
        # Basic fields
        fields.append(["Timestamp", str(self.packet.timestamp), "datetime", "0"])
        fields.append(["Device Address", self.packet.device_address, "MAC", "-"])
        fields.append(["Packet Type", self.packet.packet_type, "string", "-"])
        fields.append(["Channel", str(self.packet.channel), "uint8", "-"])
        fields.append(["RSSI", f"{self.packet.rssi} dBm", "int8", "-"])
        fields.append(["Data Length", str(len(self.packet.data)), "uint16", "-"])
        
        # Parsed fields
        if self.parsed_packet:
            if self.parsed_packet.ll_type:
                fields.append(["LL Type", self.parsed_packet.ll_type, "enum", "0"])
            
            if self.parsed_packet.l2cap_cid:
                fields.append(["L2CAP CID", f"0x{self.parsed_packet.l2cap_cid:04X}", "uint16", "2"])
            
            if self.parsed_packet.att_opcode:
                fields.append(["ATT Opcode", f"0x{self.parsed_packet.att_opcode:02X}", "uint8", "4"])
                fields.append(["ATT Operation", self.parsed_packet.att_opcode_name, "string", "-"])
            
            if self.parsed_packet.adv_local_name:
                fields.append(["Adv Name", self.parsed_packet.adv_local_name, "string", "-"])
            
            if self.parsed_packet.adv_tx_power is not None:
                fields.append(["TX Power", f"{self.parsed_packet.adv_tx_power} dBm", "int8", "-"])
        
        # Populate table
        self.fields_table.setRowCount(len(fields))
        for row, field in enumerate(fields):
            for col, value in enumerate(field):
                item = QTableWidgetItem(str(value))
                self.fields_table.setItem(row, col, item)


class PacketComparisonDialog(QDialog):
    """
    Compare multiple packets side by side
    """
    
    def __init__(self, packets: list, parent=None):
        super().__init__(parent)
        
        self.packets = packets
        
        self.setWindowTitle(f"Packet Comparison - {len(packets)} packets")
        self.setGeometry(100, 100, 1000, 600)
        
        self.init_ui()
        self.populate_comparison()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Packet Comparison")
        title.setFont(QGuiFont("Segoe UI", 14, QGuiFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Comparison table
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(len(self.packets) + 1)
        
        headers = ["Field"] + [f"Packet {i+1}" for i in range(len(self.packets))]
        self.comparison_table.setHorizontalHeaderLabels(headers)
        
        layout.addWidget(self.comparison_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def populate_comparison(self):
        """Populate comparison table"""
        # Define fields to compare
        fields = [
            ("Timestamp", lambda p: str(p.timestamp)),
            ("Address", lambda p: p.device_address),
            ("Type", lambda p: p.packet_type),
            ("Channel", lambda p: str(p.channel)),
            ("RSSI", lambda p: f"{p.rssi} dBm"),
            ("Data Length", lambda p: str(len(p.data))),
            ("Data (hex)", lambda p: p.data[:16].hex()),
        ]
        
        self.comparison_table.setRowCount(len(fields))
        
        for row, (field_name, field_func) in enumerate(fields):
            # Field name
            self.comparison_table.setItem(row, 0, QTableWidgetItem(field_name))
            
            # Values for each packet
            for col, packet in enumerate(self.packets, start=1):
                value = field_func(packet)
                item = QTableWidgetItem(value)
                
                # Highlight differences
                if col > 1:
                    prev_value = field_func(self.packets[col-2])
                    if value != prev_value:
                        item.setBackground(QBrush(QColor(255, 200, 100)))
                
                self.comparison_table.setItem(row, col, item)
        
        self.comparison_table.resizeColumnsToContents()


# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from datetime import datetime
    from backend.capture_manager import BLEPacket
    
    app = QApplication(sys.argv)
    
    # Create test packet
    test_packet = BLEPacket(
        timestamp=datetime.now(),
        device_address="AA:BB:CC:DD:EE:01",
        packet_type="ADV_IND",
        channel=37,
        rssi=-65,
        data=bytes([
            0x02, 0x01, 0x06,  # Flags
            0x0A, 0x09, 0x54, 0x65, 0x73, 0x74, 0x20, 0x44, 0x65, 0x76, 0x69, 0x63, 0x65,  # Name
            0x03, 0x03, 0xAA, 0xFE,  # Service UUID
        ])
    )
    
    # Test packet inspector
    dialog = PacketInspectorDialog(test_packet)
    dialog.exec()
    
    # Test packet comparison
    test_packets = [
        test_packet,
        BLEPacket(
            timestamp=datetime.now(),
            device_address="AA:BB:CC:DD:EE:02",
            packet_type="SCAN_RSP",
            channel=38,
            rssi=-72,
            data=bytes([0x02, 0x01, 0x06])
        )
    ]
    
    comp_dialog = PacketComparisonDialog(test_packets)
    comp_dialog.exec()
    
    sys.exit(0)

