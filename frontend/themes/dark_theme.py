"""
Dark Theme - Professional dark theme for BlueScope
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


def apply_dark_theme(app):
    """Apply dark theme to application"""
    
    # Set style
    from PyQt6.QtWidgets import QStyleFactory
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Create dark palette
    dark_palette = QPalette()
    
    # Base colors
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(212, 212, 212))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(212, 212, 212))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(212, 212, 212))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(212, 212, 212))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(212, 212, 212))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    
    # Disabled colors
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(127, 127, 127))
    
    app.setPalette(dark_palette)
    
    # Additional stylesheet
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a2a2a;
            border: 1px solid #555555;
            padding: 5px;
        }
        
        QMenuBar {
            background-color: #2d2d2d;
            color: #d4d4d4;
        }
        
        QMenuBar::item:selected {
            background-color: #3d3d3d;
        }
        
        QMenu {
            background-color: #2d2d2d;
            color: #d4d4d4;
            border: 1px solid #555555;
        }
        
        QMenu::item:selected {
            background-color: #007acc;
        }
        
        QTableWidget {
            gridline-color: #3d3d3d;
            selection-background-color: #007acc;
        }
        
        QHeaderView::section {
            background-color: #2d2d2d;
            color: #d4d4d4;
            padding: 5px;
            border: 1px solid #3d3d3d;
            font-weight: bold;
        }
        
        QTabWidget::pane {
            border: 1px solid #3d3d3d;
        }
        
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #d4d4d4;
            padding: 8px 16px;
            border: 1px solid #3d3d3d;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            border-bottom: 2px solid #007acc;
        }
        
        QTabBar::tab:hover {
            background-color: #3d3d3d;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #555555;
            min-height: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        
        QScrollBar:horizontal {
            background-color: #2d2d2d;
            height: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #555555;
            min-width: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #666666;
        }
        
        QLineEdit, QComboBox {
            background-color: #2d2d2d;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            color: #d4d4d4;
        }
        
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #007acc;
        }
        
        QPushButton {
            background-color: #2d2d2d;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px 15px;
            color: #d4d4d4;
        }
        
        QPushButton:hover {
            background-color: #3d3d3d;
            border: 1px solid #007acc;
        }
        
        QPushButton:pressed {
            background-color: #1e1e1e;
        }
        
        QStatusBar {
            background-color: #007acc;
            color: #ffffff;
        }
    """)
