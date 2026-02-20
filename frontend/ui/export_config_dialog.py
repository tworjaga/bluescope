"""
Export Configuration Dialog - UI for configuring export settings
Provides user interface for export format selection, scheduling, and options
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QSpinBox, QLineEdit, QGroupBox,
    QFormLayout, QTabWidget, QWidget, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTimeEdit, QDateEdit
)
from PyQt6.QtCore import Qt, QTime, QDate
from PyQt6.QtGui import QFont
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ExportConfigDialog(QDialog):
    """
    Export configuration dialog for BlueScope
    Allows users to configure export formats, scheduling, and options
    """
    
    def __init__(self, parent=None, current_config: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        
        self.setWindowTitle("Export Configuration")
        self.setGeometry(200, 200, 700, 500)
        
        self.config = current_config or self._default_config()
        
        self.init_ui()
        self.load_config()
        
        logger.info("ExportConfigDialog initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default export configuration"""
        return {
            'auto_export': False,
            'export_format': 'csv',
            'export_directory': './exports',
            'export_devices': True,
            'export_packets': True,
            'export_anomalies': True,
            'export_statistics': True,
            'compression': False,
            'encryption': False,
            'schedule_enabled': False,
            'schedule_interval': 300,  # 5 minutes
            'schedule_time': None,
            'filename_template': 'bluescope_export_{timestamp}',
            'max_file_size_mb': 100,
            'retention_days': 30
        }
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Export Configuration")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # General tab
        self.general_tab = self._create_general_tab()
        self.tabs.addTab(self.general_tab, "General")
        
        # Scheduling tab
        self.schedule_tab = self._create_schedule_tab()
        self.tabs.addTab(self.schedule_tab, "Scheduling")
        
        # History tab
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, "History")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
        """)
        self.save_btn.clicked.connect(self.save_config)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.test_btn = QPushButton("Test Export")
        self.test_btn.clicked.connect(self.test_export)
        
        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Export format
        self.format_combo = QComboBox()
        self.format_combo.addItems(['CSV', 'JSON', 'PCAP', 'All Formats'])
        layout.addRow("Export Format:", self.format_combo)
        
        # Export directory
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("Select export directory...")
        dir_layout.addWidget(self.dir_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_btn)
        
        layout.addRow("Export Directory:", dir_layout)
        
        # What to export
        export_group = QGroupBox("Export Contents")
        export_layout = QVBoxLayout(export_group)
        
        self.export_devices_cb = QCheckBox("Devices")
        self.export_packets_cb = QCheckBox("Packets")
        self.export_anomalies_cb = QCheckBox("Anomalies")
        self.export_stats_cb = QCheckBox("Statistics")
        
        export_layout.addWidget(self.export_devices_cb)
        export_layout.addWidget(self.export_packets_cb)
        export_layout.addWidget(self.export_anomalies_cb)
        export_layout.addWidget(self.export_stats_cb)
        
        layout.addRow(export_group)
        
        # Options
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout(options_group)
        
        self.compression_cb = QCheckBox("Enable compression (gzip)")
        self.encryption_cb = QCheckBox("Enable encryption")
        
        self.filename_template = QLineEdit()
        self.filename_template.setPlaceholderText("bluescope_export_{timestamp}")
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 1000)
        self.max_size_spin.setSuffix(" MB")
        
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 365)
        self.retention_spin.setSuffix(" days")
        
        options_layout.addRow(self.compression_cb)
        options_layout.addRow(self.encryption_cb)
        options_layout.addRow("Filename Template:", self.filename_template)
        options_layout.addRow("Max File Size:", self.max_size_spin)
        options_layout.addRow("Retention Period:", self.retention_spin)
        
        layout.addRow(options_group)
        
        return tab
    
    def _create_schedule_tab(self) -> QWidget:
        """Create scheduling tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Enable scheduling
        self.schedule_enabled_cb = QCheckBox("Enable Automatic Export Scheduling")
        self.schedule_enabled_cb.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(self.schedule_enabled_cb)
        
        # Schedule type
        schedule_group = QGroupBox("Schedule Type")
        self.schedule_type_group = QButtonGroup(self)
        
        interval_radio = QRadioButton("Interval-based")
        time_radio = QRadioButton("Time-based")
        
        self.schedule_type_group.addButton(interval_radio, 0)
        self.schedule_type_group.addButton(time_radio, 1)
        
        schedule_layout = QVBoxLayout(schedule_group)
        schedule_layout.addWidget(interval_radio)
        schedule_layout.addWidget(time_radio)
        
        layout.addWidget(schedule_group)
        
        # Interval settings
        interval_group = QGroupBox("Interval Settings")
        interval_layout = QFormLayout(interval_group)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setSuffix(" minutes")
        
        interval_layout.addRow("Export Interval:", self.interval_spin)
        
        layout.addWidget(interval_group)
        
        # Time-based settings
        time_group = QGroupBox("Time-based Settings")
        time_layout = QFormLayout(time_group)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        time_layout.addRow("Export Time:", self.time_edit)
        time_layout.addRow("Start Date:", self.date_edit)
        
        layout.addWidget(time_group)
        
        # Auto-export on events
        events_group = QGroupBox("Event-based Export")
        events_layout = QVBoxLayout(events_group)
        
        self.export_on_anomaly_cb = QCheckBox("Export when anomaly detected")
        self.export_on_device_cb = QCheckBox("Export when new device discovered")
        self.export_on_stop_cb = QCheckBox("Export when capture stops")
        
        events_layout.addWidget(self.export_on_anomaly_cb)
        events_layout.addWidget(self.export_on_device_cb)
        events_layout.addWidget(self.export_on_stop_cb)
        
        layout.addWidget(events_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_history_tab(self) -> QWidget:
        """Create export history tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Format", "Size", "Status", "File", "Actions"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        
        layout.addWidget(self.history_table)
        
        # History buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_history_btn = QPushButton("Refresh")
        self.refresh_history_btn.clicked.connect(self.refresh_history)
        
        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.clicked.connect(self.clear_history)
        
        self.open_folder_btn = QPushButton("Open Export Folder")
        self.open_folder_btn.clicked.connect(self.open_export_folder)
        
        btn_layout.addWidget(self.refresh_history_btn)
        btn_layout.addWidget(self.clear_history_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.open_folder_btn)
        
        layout.addLayout(btn_layout)
        
        return tab
    
    def browse_directory(self):
        """Open directory browser dialog"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            self.dir_edit.text() or "."
        )
        
        if directory:
            self.dir_edit.setText(directory)
    
    def load_config(self):
        """Load configuration into UI"""
        # General tab
        format_map = {'csv': 0, 'json': 1, 'pcap': 2, 'all': 3}
        self.format_combo.setCurrentIndex(
            format_map.get(self.config.get('export_format', 'csv'), 0)
        )
        
        self.dir_edit.setText(self.config.get('export_directory', './exports'))
        
        self.export_devices_cb.setChecked(
            self.config.get('export_devices', True)
        )
        self.export_packets_cb.setChecked(
            self.config.get('export_packets', True)
        )
        self.export_anomalies_cb.setChecked(
            self.config.get('export_anomalies', True)
        )
        self.export_stats_cb.setChecked(
            self.config.get('export_statistics', True)
        )
        
        self.compression_cb.setChecked(
            self.config.get('compression', False)
        )
        self.encryption_cb.setChecked(
            self.config.get('encryption', False)
        )
        
        self.filename_template.setText(
            self.config.get('filename_template', 'bluescope_export_{timestamp}')
        )
        
        self.max_size_spin.setValue(
            self.config.get('max_file_size_mb', 100)
        )
        
        self.retention_spin.setValue(
            self.config.get('retention_days', 30)
        )
        
        # Schedule tab
        self.schedule_enabled_cb.setChecked(
            self.config.get('schedule_enabled', False)
        )
        
        interval_minutes = self.config.get('schedule_interval', 300) // 60
        self.interval_spin.setValue(interval_minutes)
        
        # History tab
        self.refresh_history()
    
    def save_config(self):
        """Save configuration from UI"""
        # General tab
        format_map = {0: 'csv', 1: 'json', 2: 'pcap', 3: 'all'}
        self.config['export_format'] = format_map.get(
            self.format_combo.currentIndex(), 'csv'
        )
        
        self.config['export_directory'] = self.dir_edit.text()
        
        self.config['export_devices'] = self.export_devices_cb.isChecked()
        self.config['export_packets'] = self.export_packets_cb.isChecked()
        self.config['export_anomalies'] = self.export_anomalies_cb.isChecked()
        self.config['export_statistics'] = self.export_stats_cb.isChecked()
        
        self.config['compression'] = self.compression_cb.isChecked()
        self.config['encryption'] = self.encryption_cb.isChecked()
        
        self.config['filename_template'] = self.filename_template.text()
        self.config['max_file_size_mb'] = self.max_size_spin.value()
        self.config['retention_days'] = self.retention_spin.value()
        
        # Schedule tab
        self.config['schedule_enabled'] = self.schedule_enabled_cb.isChecked()
        self.config['schedule_interval'] = self.interval_spin.value() * 60
        
        logger.info("Export configuration saved")
        
        self.accept()
    
    def get_config(self) -> Dict[str, Any]:
        """Return current configuration"""
        return self.config.copy()
    
    def test_export(self):
        """Test export with current settings"""
        QMessageBox.information(
            self,
            "Test Export",
            "Export test would be performed here with current settings.\n"
            f"Format: {self.format_combo.currentText()}\n"
            f"Directory: {self.dir_edit.text()}\n\n"
            "In a real implementation, this would create a test export."
        )
    
    def refresh_history(self):
        """Refresh export history table"""
        # In a real implementation, this would load from export_manager history
        self.history_table.setRowCount(0)  # Clear
        
        # Add sample data
        sample_data = [
            ["2025-01-20 10:30:00", "CSV", "1.2 MB", "Success", "export_001.csv", "Open"],
            ["2025-01-20 10:15:00", "JSON", "2.5 MB", "Success", "export_002.json", "Open"],
            ["2025-01-20 10:00:00", "PCAP", "5.1 MB", "Success", "export_003.pcap", "Open"],
        ]
        
        for row_data in sample_data:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                self.history_table.setItem(row, col, item)
    
    def clear_history(self):
        """Clear export history"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the export history?\n"
            "This will not delete the exported files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_table.setRowCount(0)
            logger.info("Export history cleared")
    
    def open_export_folder(self):
        """Open export directory in file manager"""
        import os
        import platform
        import subprocess
        
        directory = self.dir_edit.text()
        
        if not os.path.exists(directory):
            QMessageBox.warning(
                self,
                "Directory Not Found",
                f"The export directory does not exist:\n{directory}"
            )
            return
        
        try:
            if platform.system() == "Windows":
                os.startfile(directory)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", directory])
            else:  # Linux
                subprocess.call(["xdg-open", directory])
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not open directory: {e}"
            )


class QuickExportDialog(QDialog):
    """
    Quick export dialog for fast exports
    Simplified version for common use cases
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Quick Export")
        self.setGeometry(300, 300, 400, 300)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Quick Export")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        self.csv_radio = QRadioButton("CSV (Spreadsheet)")
        self.json_radio = QRadioButton("JSON (Raw Data)")
        self.pcap_radio = QRadioButton("PCAP (Wireshark)")
        
        self.csv_radio.setChecked(True)
        
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.json_radio)
        format_layout.addWidget(self.pcap_radio)
        
        layout.addWidget(format_group)
        
        # What to export
        content_group = QGroupBox("Export Contents")
        content_layout = QVBoxLayout(content_group)
        
        self.devices_cb = QCheckBox("Devices")
        self.packets_cb = QCheckBox("Packets")
        self.anomalies_cb = QCheckBox("Anomalies")
        
        self.devices_cb.setChecked(True)
        self.packets_cb.setChecked(True)
        
        content_layout.addWidget(self.devices_cb)
        content_layout.addWidget(self.packets_cb)
        content_layout.addWidget(self.anomalies_cb)
        
        layout.addWidget(content_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                padding: 8px 16px;
            }
        """)
        self.export_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.export_btn)
        
        layout.addLayout(btn_layout)
    
    def get_export_options(self) -> Dict[str, Any]:
        """Get selected export options"""
        if self.csv_radio.isChecked():
            format_type = 'csv'
        elif self.json_radio.isChecked():
            format_type = 'json'
        else:
            format_type = 'pcap'
        
        return {
            'format': format_type,
            'export_devices': self.devices_cb.isChecked(),
            'export_packets': self.packets_cb.isChecked(),
            'export_anomalies': self.anomalies_cb.isChecked()
        }


# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test full config dialog
    dialog = ExportConfigDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Configuration saved:")
        print(dialog.get_config())
    
    # Test quick export dialog
    quick_dialog = QuickExportDialog()
    if quick_dialog.exec() == QDialog.DialogCode.Accepted:
        print("Quick export options:")
        print(quick_dialog.get_export_options())
    
    sys.exit(0)
