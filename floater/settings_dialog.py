"""
Settings Dialog for hndl-it Floater UI.
Allows customization of themes, modes, and agent connections.
"""
import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QGroupBox, QFormLayout, QLineEdit,
    QCheckBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)
    
    # Color themes
    THEMES = {
        "orange": {
            "name": "Warm Orange",
            "bg": "rgba(50, 40, 30, 230)",
            "border": "rgba(255, 160, 80, 180)",
            "accent": "#ffaa44",
            "text": "#ffffff",
            "text_secondary": "#ffcc99",
        },
        "blue": {
            "name": "Cool Blue",
            "bg": "rgba(30, 40, 60, 230)",
            "border": "rgba(80, 160, 255, 180)",
            "accent": "#66aaff",
            "text": "#ffffff",
            "text_secondary": "#aaccff",
        },
        "green": {
            "name": "Matrix Green",
            "bg": "rgba(20, 35, 25, 230)",
            "border": "rgba(80, 200, 120, 180)",
            "accent": "#44dd88",
            "text": "#ffffff",
            "text_secondary": "#aaffcc",
        },
        "purple": {
            "name": "Neon Purple",
            "bg": "rgba(40, 30, 50, 230)",
            "border": "rgba(180, 100, 255, 180)",
            "accent": "#bb66ff",
            "text": "#ffffff",
            "text_secondary": "#ddaaff",
        },
        "dark": {
            "name": "Dark Mode",
            "bg": "rgba(25, 25, 25, 240)",
            "border": "rgba(80, 80, 80, 180)",
            "accent": "#888888",
            "text": "#ffffff",
            "text_secondary": "#aaaaaa",
        },
    }
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("hndl-it Settings")
        self.setFixedSize(400, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #ffaa44;
            }
            QLabel {
                color: #cccccc;
            }
            QComboBox, QLineEdit {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 3px;
                color: #fff;
                padding: 5px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #444;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffaa44;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QPushButton {
                background-color: #444;
                color: #fff;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton#SaveBtn {
                background-color: #ff8844;
                border: none;
            }
            QPushButton#SaveBtn:hover {
                background-color: #ff9955;
            }
            QCheckBox {
                color: #cccccc;
            }
        """)
        
        self.current_settings = current_settings or self._get_defaults()
        self._setup_ui()
        self._load_settings()
    
    def _get_defaults(self):
        return {
            "theme": "orange",
            "default_mode": "full",
            "opacity_normal": 100,
            "opacity_ghost": 30,
            "start_minimized": False,
            "auto_hide_on_command": False,
            "browser_port": 8766,
            "desktop_port": 8767,
            "vision_port": 8768,
        }
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget()
        
        # --- Appearance Tab ---
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        # Theme
        theme_group = QGroupBox("Color Theme")
        theme_layout = QFormLayout(theme_group)
        self.theme_combo = QComboBox()
        for key, theme in self.THEMES.items():
            self.theme_combo.addItem(theme["name"], key)
        theme_layout.addRow("Theme:", self.theme_combo)
        appearance_layout.addWidget(theme_group)
        
        # Mode
        mode_group = QGroupBox("Default UI Mode")
        mode_layout = QFormLayout(mode_group)
        self.mode_combo = QComboBox()
        for mode in ["full", "bar", "pill", "panel", "tray"]:
            self.mode_combo.addItem(mode.capitalize(), mode)
        mode_layout.addRow("Start in:", self.mode_combo)
        appearance_layout.addWidget(mode_group)
        
        # Opacity
        opacity_group = QGroupBox("Transparency")
        opacity_layout = QFormLayout(opacity_group)
        
        self.opacity_normal_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_normal_slider.setRange(20, 100)
        self.opacity_normal_label = QLabel("100%")
        self.opacity_normal_slider.valueChanged.connect(
            lambda v: self.opacity_normal_label.setText(f"{v}%")
        )
        opacity_layout.addRow("Normal:", self.opacity_normal_slider)
        opacity_layout.addRow("", self.opacity_normal_label)
        
        self.opacity_ghost_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_ghost_slider.setRange(10, 80)
        self.opacity_ghost_label = QLabel("30%")
        self.opacity_ghost_slider.valueChanged.connect(
            lambda v: self.opacity_ghost_label.setText(f"{v}%")
        )
        opacity_layout.addRow("Ghost:", self.opacity_ghost_slider)
        opacity_layout.addRow("", self.opacity_ghost_label)
        
        appearance_layout.addWidget(opacity_group)
        appearance_layout.addStretch()
        
        tabs.addTab(appearance_tab, "Appearance")
        
        # --- Behavior Tab ---
        behavior_tab = QWidget()
        behavior_layout = QVBoxLayout(behavior_tab)
        
        behavior_group = QGroupBox("Behavior")
        behavior_form = QFormLayout(behavior_group)
        
        self.start_minimized_check = QCheckBox("Start minimized to tray")
        behavior_form.addRow(self.start_minimized_check)
        
        self.auto_hide_check = QCheckBox("Auto-hide after command")
        behavior_form.addRow(self.auto_hide_check)
        
        behavior_layout.addWidget(behavior_group)
        behavior_layout.addStretch()
        
        tabs.addTab(behavior_tab, "Behavior")
        
        # --- Connections Tab ---
        connections_tab = QWidget()
        connections_layout = QVBoxLayout(connections_tab)
        
        ports_group = QGroupBox("Agent Ports")
        ports_layout = QFormLayout(ports_group)
        
        self.browser_port_input = QLineEdit()
        ports_layout.addRow("Browser Agent:", self.browser_port_input)
        
        self.desktop_port_input = QLineEdit()
        ports_layout.addRow("Desktop Agent:", self.desktop_port_input)
        
        self.vision_port_input = QLineEdit()
        ports_layout.addRow("Vision Agent:", self.vision_port_input)
        
        connections_layout.addWidget(ports_group)
        connections_layout.addStretch()
        
        tabs.addTab(connections_tab, "Connections")
        
        layout.addWidget(tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_settings(self):
        """Load current settings into UI."""
        s = self.current_settings
        
        # Theme
        idx = self.theme_combo.findData(s.get("theme", "orange"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        
        # Mode
        idx = self.mode_combo.findData(s.get("default_mode", "full"))
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        
        # Opacity
        self.opacity_normal_slider.setValue(s.get("opacity_normal", 100))
        self.opacity_ghost_slider.setValue(s.get("opacity_ghost", 30))
        
        # Behavior
        self.start_minimized_check.setChecked(s.get("start_minimized", False))
        self.auto_hide_check.setChecked(s.get("auto_hide_on_command", False))
        
        # Ports
        self.browser_port_input.setText(str(s.get("browser_port", 8766)))
        self.desktop_port_input.setText(str(s.get("desktop_port", 8767)))
        self.vision_port_input.setText(str(s.get("vision_port", 8768)))
    
    def _reset_defaults(self):
        """Reset all settings to defaults."""
        self.current_settings = self._get_defaults()
        self._load_settings()
    
    def _save_settings(self):
        """Save settings and emit signal."""
        settings = {
            "theme": self.theme_combo.currentData(),
            "default_mode": self.mode_combo.currentData(),
            "opacity_normal": self.opacity_normal_slider.value(),
            "opacity_ghost": self.opacity_ghost_slider.value(),
            "start_minimized": self.start_minimized_check.isChecked(),
            "auto_hide_on_command": self.auto_hide_check.isChecked(),
            "browser_port": int(self.browser_port_input.text() or 8766),
            "desktop_port": int(self.desktop_port_input.text() or 8767),
            "vision_port": int(self.vision_port_input.text() or 8768),
        }
        
        self.settings_changed.emit(settings)
        self.accept()
    
    @classmethod
    def get_theme_styles(cls, theme_key: str) -> dict:
        """Get theme colors by key."""
        return cls.THEMES.get(theme_key, cls.THEMES["orange"])
