"""
Alert Notification System - Real-time anomaly alerts and notifications
Provides visual and audio alerts for detected anomalies
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QCheckBox, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QWidget, QTextEdit, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette
from PyQt6.QtMultimedia import QSoundEffect

from backend.ml_integration import AnomalyAlert

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertNotificationManager(QObject):
    """
    Manages alert notifications for the application
    Provides visual alerts, system tray notifications, and sound alerts
    """
    
    alert_triggered = pyqtSignal(object)  # AnomalyAlert
    alert_acknowledged = pyqtSignal(str)  # alert_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Alert storage
        self.alerts: List[AnomalyAlert] = []
        self.unacknowledged_alerts: List[AnomalyAlert] = []
        
        # Settings
        self.settings = {
            'enabled': True,
            'show_notifications': True,
            'play_sounds': True,
            'min_severity': AlertSeverity.MEDIUM,
            'auto_acknowledge_after': 300,  # 5 minutes
            'max_alerts': 100
        }
        
        # Callbacks
        self.on_alert: Optional[Callable[[AnomalyAlert], None]] = None
        self.on_acknowledge: Optional[Callable[[str], None]] = None
        
        # System tray
        self.tray_icon: Optional[QSystemTrayIcon] = None
        
        # Sound effects
        self.alert_sound: Optional[QSoundEffect] = None
        self._init_sound()
        
        # Auto-acknowledge timer
        self.ack_timer = QTimer()
        self.ack_timer.timeout.connect(self._auto_acknowledge_old_alerts)
        self.ack_timer.start(60000)  # Check every minute
        
        logger.info("AlertNotificationManager initialized")
    
    def _init_sound(self):
        """Initialize sound effects"""
        try:
            self.alert_sound = QSoundEffect()
            # Note: In a real implementation, you would load a sound file
            # self.alert_sound.setSource(QUrl.fromLocalFile("alert.wav"))
        except Exception as e:
            logger.warning(f"Could not initialize sound: {e}")
    
    def set_tray_icon(self, tray_icon: QSystemTrayIcon):
        """Set system tray icon for notifications"""
        self.tray_icon = tray_icon
    
    def trigger_alert(self, alert: AnomalyAlert):
        """
        Trigger an alert notification
        
        Args:
            alert: AnomalyAlert to display
        """
        if not self.settings['enabled']:
            return
        
        # Check severity threshold
        severity_levels = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        alert_level = severity_levels.get(alert.severity, 0)
        min_level = severity_levels.get(self.settings['min_severity'].value, 0)
        
        if alert_level < min_level:
            return
        
        # Add to lists
        self.alerts.append(alert)
        self.unacknowledged_alerts.append(alert)
        
        # Limit max alerts
        if len(self.alerts) > self.settings['max_alerts']:
            self.alerts = self.alerts[-self.settings['max_alerts']:]
        
        # Emit signal
        self.alert_triggered.emit(alert)
        
        # Show notification
        if self.settings['show_notifications']:
            self._show_notification(alert)
        
        # Play sound
        if self.settings['play_sounds'] and self.alert_sound:
            self._play_alert_sound(alert.severity)
        
        # Call callback
        if self.on_alert:
            self.on_alert(alert)
        
        logger.warning(f"Alert triggered: {alert.description} ({alert.severity})")
    
    def _show_notification(self, alert: AnomalyAlert):
        """Show system tray notification"""
        if self.tray_icon and self.tray_icon.supportsMessages():
            title = f"BlueScope Alert - {alert.severity.upper()}"
            message = f"{alert.device_name}: {alert.description}"
            
            icon = QSystemTrayIcon.MessageIcon.Warning
            if alert.severity == 'critical':
                icon = QSystemTrayIcon.MessageIcon.Critical
            elif alert.severity == 'low':
                icon = QSystemTrayIcon.MessageIcon.Information
            
            self.tray_icon.showMessage(title, message, icon, 5000)
    
    def _play_alert_sound(self, severity: str):
        """Play alert sound based on severity"""
        if not self.alert_sound:
            return
        
        # Different sounds for different severities
        # In a real implementation, you would have different sound files
        try:
            self.alert_sound.play()
        except Exception as e:
            logger.debug(f"Could not play alert sound: {e}")
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: ID of alert to acknowledge
        
        Returns:
            True if acknowledged successfully
        """
        for alert in self.unacknowledged_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.unacknowledged_alerts.remove(alert)
                
                self.alert_acknowledged.emit(alert_id)
                
                if self.on_acknowledge:
                    self.on_acknowledge(alert_id)
                
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
        
        return False
    
    def acknowledge_all(self):
        """Acknowledge all unacknowledged alerts"""
        for alert in self.unacknowledged_alerts:
            alert.acknowledged = True
            self.alert_acknowledged.emit(alert.alert_id)
        
        self.unacknowledged_alerts.clear()
        logger.info("All alerts acknowledged")
    
    def _auto_acknowledge_old_alerts(self):
        """Auto-acknowledge old alerts"""
        if self.settings['auto_acknowledge_after'] <= 0:
            return
        
        now = datetime.now()
        to_acknowledge = []
        
        for alert in self.unacknowledged_alerts:
            age = (now - alert.timestamp).total_seconds()
            if age > self.settings['auto_acknowledge_after']:
                to_acknowledge.append(alert.alert_id)
        
        for alert_id in to_acknowledge:
            self.acknowledge_alert(alert_id)
            logger.debug(f"Auto-acknowledged alert: {alert_id}")
    
    def get_alerts(self, severity: Optional[str] = None,
                  acknowledged: Optional[bool] = None,
                  limit: int = 100) -> List[AnomalyAlert]:
        """
        Get alerts with optional filtering
        
        Args:
            severity: Filter by severity
            acknowledged: Filter by acknowledged status
            limit: Maximum number of alerts to return
        
        Returns:
            List of AnomalyAlert objects
        """
        filtered = self.alerts
        
        if severity:
            filtered = [a for a in filtered if a.severity == severity]
        
        if acknowledged is not None:
            filtered = [a for a in filtered if a.acknowledged == acknowledged]
        
        return filtered[-limit:]
    
    def get_unacknowledged_count(self) -> int:
        """Get count of unacknowledged alerts"""
        return len(self.unacknowledged_alerts)
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total = len(self.alerts)
        unacknowledged = len(self.unacknowledged_alerts)
        
        by_severity = {}
        for alert in self.alerts:
            by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1
        
        return {
            'total': total,
            'unacknowledged': unacknowledged,
            'acknowledged': total - unacknowledged,
            'by_severity': by_severity
        }
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update alert settings"""
        self.settings.update(settings)
        logger.info(f"Alert settings updated: {settings}")
    
    def clear_all_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
        self.unacknowledged_alerts.clear()
        logger.info("All alerts cleared")


class AlertPanel(QWidget):
    """
    Alert panel for displaying alerts in the GUI
    """
    
    alert_selected = pyqtSignal(object)  # AnomalyAlert
    
    def __init__(self, alert_manager: AlertNotificationManager, parent=None):
        super().__init__(parent)
        
        self.alert_manager = alert_manager
        
        self.init_ui()
        
        # Connect signals
        self.alert_manager.alert_triggered.connect(self.on_new_alert)
        self.alert_manager.alert_acknowledged.connect(self.on_alert_acknowledged)
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Anomaly Alerts")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Alert count badge
        self.alert_count_label = QLabel("0")
        self.alert_count_label.setStyleSheet("""
            QLabel {
                background-color: #F44336;
                color: white;
                padding: 4px 8px;
                border-radius: 10px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(self.alert_count_label)
        
        # Acknowledge all button
        self.ack_all_btn = QPushButton("Acknowledge All")
        self.ack_all_btn.clicked.connect(self.acknowledge_all)
        header_layout.addWidget(self.ack_all_btn)
        
        layout.addLayout(header_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Severity:"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.severity_filter.currentTextChanged.connect(self.refresh_alerts)
        filter_layout.addWidget(self.severity_filter)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Unacknowledged", "Acknowledged"])
        self.status_filter.currentTextChanged.connect(self.refresh_alerts)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(6)
        self.alerts_table.setHorizontalHeaderLabels([
            "Time", "Severity", "Device", "Type", "Description", "Status"
        ])
        self.alerts_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.alerts_table.itemClicked.connect(self.on_alert_clicked)
        
        layout.addWidget(self.alerts_table)
        
        # Alert details
        self.details_group = QGroupBox("Alert Details")
        details_layout = QFormLayout(self.details_group)
        
        self.detail_id = QLabel()
        self.detail_timestamp = QLabel()
        self.detail_device = QLabel()
        self.detail_severity = QLabel()
        self.detail_score = QLabel()
        self.detail_description = QTextEdit()
        self.detail_description.setReadOnly(True)
        self.detail_description.setMaximumHeight(80)
        
        details_layout.addRow("ID:", self.detail_id)
        details_layout.addRow("Timestamp:", self.detail_timestamp)
        details_layout.addRow("Device:", self.detail_device)
        details_layout.addRow("Severity:", self.detail_severity)
        details_layout.addRow("Score:", self.detail_score)
        details_layout.addRow("Description:", self.detail_description)
        
        # Acknowledge button
        self.ack_btn = QPushButton("Acknowledge Alert")
        self.ack_btn.clicked.connect(self.acknowledge_selected)
        self.ack_btn.setEnabled(False)
        details_layout.addRow(self.ack_btn)
        
        layout.addWidget(self.details_group)
        
        # Selected alert
        self.selected_alert: Optional[AnomalyAlert] = None
    
    def on_new_alert(self, alert: AnomalyAlert):
        """Handle new alert"""
        self.refresh_alerts()
        self.update_alert_count()
    
    def on_alert_acknowledged(self, alert_id: str):
        """Handle alert acknowledgement"""
        self.refresh_alerts()
        self.update_alert_count()
    
    def refresh_alerts(self):
        """Refresh alerts table"""
        # Get filter settings
        severity = self.severity_filter.currentText().lower()
        if severity == "all":
            severity = None
        
        status = self.status_filter.currentText().lower()
        if status == "all":
            acknowledged = None
        elif status == "acknowledged":
            acknowledged = True
        else:  # unacknowledged
            acknowledged = False
        
        # Get alerts
        alerts = self.alert_manager.get_alerts(
            severity=severity,
            acknowledged=acknowledged,
            limit=100
        )
        
        # Populate table
        self.alerts_table.setRowCount(len(alerts))
        
        for row, alert in enumerate(alerts):
            self.alerts_table.setItem(row, 0, QTableWidgetItem(
                alert.timestamp.strftime("%H:%M:%S")
            ))
            
            severity_item = QTableWidgetItem(alert.severity.upper())
            # Color code severity
            colors = {
                'critical': QColor(244, 67, 54),  # Red
                'high': QColor(255, 152, 0),     # Orange
                'medium': QColor(255, 235, 59),  # Yellow
                'low': QColor(76, 175, 80)       # Green
            }
            severity_item.setBackground(QBrush(colors.get(alert.severity, QColor(128, 128, 128))))
            self.alerts_table.setItem(row, 1, severity_item)
            
            self.alerts_table.setItem(row, 2, QTableWidgetItem(alert.device_name))
            self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.anomaly_type))
            self.alerts_table.setItem(row, 4, QTableWidgetItem(alert.description[:50]))
            
            status = "Acknowledged" if alert.acknowledged else "New"
            self.alerts_table.setItem(row, 5, QTableWidgetItem(status))
            
            # Store alert in item data
            for col in range(6):
                item = self.alerts_table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, alert)
    
    def update_alert_count(self):
        """Update alert count badge"""
        count = self.alert_manager.get_unacknowledged_count()
        self.alert_count_label.setText(str(count))
        
        # Hide badge if no alerts
        self.alert_count_label.setVisible(count > 0)
    
    def on_alert_clicked(self, item: QTableWidgetItem):
        """Handle alert selection"""
        alert = item.data(Qt.ItemDataRole.UserRole)
        if alert:
            self.selected_alert = alert
            self.display_alert_details(alert)
            self.alert_selected.emit(alert)
    
    def display_alert_details(self, alert: AnomalyAlert):
        """Display alert details"""
        self.detail_id.setText(alert.alert_id)
        self.detail_timestamp.setText(str(alert.timestamp))
        self.detail_device.setText(f"{alert.device_name} ({alert.device_address})")
        self.detail_severity.setText(alert.severity.upper())
        self.detail_score.setText(f"{alert.score:.2f}")
        self.detail_description.setText(alert.description)
        
        self.ack_btn.setEnabled(not alert.acknowledged)
    
    def acknowledge_selected(self):
        """Acknowledge selected alert"""
        if self.selected_alert:
            self.alert_manager.acknowledge_alert(self.selected_alert.alert_id)
            self.ack_btn.setEnabled(False)
    
    def acknowledge_all(self):
        """Acknowledge all alerts"""
        self.alert_manager.acknowledge_all()


# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from datetime import datetime
    
    app = QApplication(sys.argv)
    
    # Create alert manager
    alert_manager = AlertNotificationManager()
    
    # Create test alerts
    test_alerts = [
        AnomalyAlert(
            alert_id="ALT-000001",
            timestamp=datetime.now(),
            device_address="AA:BB:CC:DD:EE:01",
            device_name="Test Device 1",
            anomaly_type="High Packet Rate",
            severity="high",
            score=0.85,
            description="Device is sending packets at an unusually high rate"
        ),
        AnomalyAlert(
            alert_id="ALT-000002",
            timestamp=datetime.now(),
            device_address="AA:BB:CC:DD:EE:02",
            device_name="Test Device 2",
            anomaly_type="Unusual RSSI",
            severity="medium",
            score=0.72,
            description="RSSI values are outside normal range"
        ),
    ]
    
    # Create panel
    panel = AlertPanel(alert_manager)
    panel.setWindowTitle("Alert Panel Test")
    panel.resize(800, 600)
    
    # Trigger test alerts
    for alert in test_alerts:
        alert_manager.trigger_alert(alert)
    
    panel.show()
    
    sys.exit(app.exec())

