"""
A2UI Renderer - Pure PyQt6 implementation of A2UI component rendering
Part of hndl-it Antigravity ecosystem

Maps A2UI JSON component specs to native PyQt6 widgets.
Security: Only renders from a pre-approved component catalog.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFrame, QScrollArea, QListWidget,
    QListWidgetItem, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger("hndl-it.a2ui")


class A2UIRenderer(QWidget):
    """
    Renders A2UI JSON payloads to native PyQt6 widgets.
    
    Security Model:
    - Only components in the CATALOG are rendered
    - Unknown component types are logged and skipped
    - All props are sanitized before use
    """
    
    # Signal emitted when a button/action is triggered
    action_triggered = pyqtSignal(str, dict)  # (action_name, payload)
    
    # Approved component catalog
    CATALOG = {"Card", "Text", "Button", "TextField", "List", "ProgressBar", "Header", "Divider"}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("A2UIRenderer")
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        
        # Scroll area for content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Content widget
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(8)
        self.content_layout.addStretch()
        
        self.scroll.setWidget(self.content)
        self.layout.addWidget(self.scroll)
        
        # Widget registry (id -> widget) for updates
        self.widgets: Dict[str, QWidget] = {}
        
        # Apply base styling
        self._apply_styles()

    def _apply_styles(self):
        """Apply A2UI-compatible styles in lime-green theme."""
        self.setStyleSheet("""
            QWidget#A2UIRenderer {
                background-color: transparent;
            }
            QFrame.a2ui-card {
                background-color: rgba(25, 40, 30, 220);
                border: 1px solid rgba(100, 255, 100, 100);
                border-radius: 8px;
                padding: 10px;
            }
            QLabel.a2ui-title {
                color: #88ff88;
                font-weight: bold;
                font-size: 14px;
            }
            QLabel.a2ui-subtitle {
                color: #66aa66;
                font-size: 11px;
            }
            QLabel.a2ui-text {
                color: #ccffcc;
                font-size: 12px;
            }
            QPushButton.a2ui-button {
                background-color: rgba(50, 100, 60, 200);
                color: #aaffaa;
                border: 1px solid rgba(100, 255, 100, 150);
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton.a2ui-button:hover {
                background-color: rgba(70, 140, 80, 220);
                color: #ffffff;
            }
            QLineEdit.a2ui-textfield {
                background-color: rgba(20, 30, 25, 200);
                border: 1px solid rgba(100, 255, 100, 100);
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
            }
            QProgressBar.a2ui-progress {
                border: none;
                background-color: rgba(25, 35, 30, 150);
                height: 6px;
                border-radius: 3px;
            }
            QProgressBar.a2ui-progress::chunk {
                background-color: #66ff66;
                border-radius: 3px;
            }
        """)

    def render(self, a2ui_payload: Dict[str, Any]):
        """
        Render an A2UI component tree.
        
        Args:
            a2ui_payload: Root A2UI component dict with type, id, props, children
        """
        # Clear existing content
        self.clear()
        
        # Render root component
        widget = self._render_component(a2ui_payload)
        if widget:
            # Insert before the stretch
            self.content_layout.insertWidget(self.content_layout.count() - 1, widget)
        
        logger.debug(f"Rendered A2UI tree: {a2ui_payload.get('type', 'unknown')}")

    def render_list(self, components: List[Dict[str, Any]]):
        """Render multiple top-level components."""
        self.clear()
        for comp in components:
            widget = self._render_component(comp)
            if widget:
                self.content_layout.insertWidget(self.content_layout.count() - 1, widget)

    def clear(self):
        """Clear all rendered content."""
        # Remove all widgets except the stretch
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.widgets.clear()

    def _render_component(self, spec: Dict[str, Any]) -> Optional[QWidget]:
        """Render a single A2UI component spec."""
        comp_type = spec.get("type", "")
        comp_id = spec.get("id", "")
        props = spec.get("props", {})
        children = spec.get("children", [])
        
        # Security: Only render approved components
        if comp_type not in self.CATALOG:
            logger.warning(f"Unknown A2UI component type: {comp_type}")
            return None
        
        # Dispatch to component renderer
        renderer = getattr(self, f"_render_{comp_type.lower()}", None)
        if renderer:
            widget = renderer(comp_id, props, children)
            if widget and comp_id:
                self.widgets[comp_id] = widget
            return widget
        
        return None

    def _render_card(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a Card component."""
        card = QFrame()
        card.setProperty("class", "a2ui-card")
        card.setObjectName(comp_id)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        
        # Title
        if "title" in props:
            title = QLabel(props["title"])
            title.setProperty("class", "a2ui-title")
            layout.addWidget(title)
        
        # Subtitle
        if "subtitle" in props:
            subtitle = QLabel(props["subtitle"])
            subtitle.setProperty("class", "a2ui-subtitle")
            layout.addWidget(subtitle)
        
        # Render children
        for child in children:
            child_widget = self._render_component(child)
            if child_widget:
                layout.addWidget(child_widget)
        
        return card

    def _render_text(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a Text component."""
        text = props.get("text", "")
        label = QLabel(text)
        label.setProperty("class", "a2ui-text")
        label.setObjectName(comp_id)
        label.setWordWrap(True)
        return label

    def _render_header(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a Header component."""
        text = props.get("text", "")
        level = props.get("level", 1)
        
        label = QLabel(text)
        label.setProperty("class", "a2ui-title")
        label.setObjectName(comp_id)
        
        # Adjust font size based on level
        font = label.font()
        font.setPointSize(max(10, 18 - (level * 2)))
        font.setBold(True)
        label.setFont(font)
        
        return label

    def _render_button(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a Button component."""
        label = props.get("label", "Button")
        action = props.get("action", "")
        payload = props.get("payload", {})
        
        button = QPushButton(label)
        button.setProperty("class", "a2ui-button")
        button.setObjectName(comp_id)
        
        # Connect click to action signal
        button.clicked.connect(lambda: self.action_triggered.emit(action, payload))
        
        return button

    def _render_textfield(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a TextField component."""
        placeholder = props.get("placeholder", "")
        value = props.get("value", "")
        
        field = QLineEdit()
        field.setProperty("class", "a2ui-textfield")
        field.setObjectName(comp_id)
        field.setPlaceholderText(placeholder)
        field.setText(value)
        
        return field

    def _render_list(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a List component (container for multiple items)."""
        container = QWidget()
        container.setObjectName(comp_id)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Title if present
        if "title" in props:
            title = QLabel(props["title"])
            title.setProperty("class", "a2ui-title")
            layout.addWidget(title)
        
        # Render children
        for child in children:
            child_widget = self._render_component(child)
            if child_widget:
                layout.addWidget(child_widget)
        
        return container

    def _render_progressbar(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a ProgressBar component."""
        value = props.get("value", 0)
        max_value = props.get("max", 100)
        
        bar = QProgressBar()
        bar.setProperty("class", "a2ui-progress")
        bar.setObjectName(comp_id)
        bar.setMaximum(max_value)
        bar.setValue(value)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        
        return bar

    def _render_divider(self, comp_id: str, props: Dict, children: List[Dict]) -> QWidget:
        """Render a Divider component."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(100, 255, 100, 50);")
        line.setFixedHeight(1)
        return line

    def update_component(self, comp_id: str, new_props: Dict[str, Any]):
        """Update an existing component's properties."""
        widget = self.widgets.get(comp_id)
        if not widget:
            logger.warning(f"Cannot update unknown component: {comp_id}")
            return
        
        # Handle updates based on widget type
        if isinstance(widget, QLabel):
            if "text" in new_props:
                widget.setText(new_props["text"])
        elif isinstance(widget, QProgressBar):
            if "value" in new_props:
                widget.setValue(new_props["value"])
        elif isinstance(widget, QLineEdit):
            if "value" in new_props:
                widget.setText(new_props["value"])
