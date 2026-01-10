"""
todo-it: Smart Todo List Module for hndl-it
Features:
- Slide-out panel (1.5x hndl-it size)
- Items with check/remove/highlight/expand
- Sub-notes + links (websites, docs, anything)
- One-click input, two-click full panel
- Date/time logging
- Tags and search
"""

import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QFrame, QLabel, QMenu,
    QTextEdit, QSplitter, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QColor, QBrush, QAction, QIcon

# Colors matching hndl-it theme
COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_panel': '#16213e',
    'primary': '#e67e22',  # Orange
    'secondary': '#00d4ff',  # Cyan
    'accent': '#00ff88',  # Green for completed
    'text': '#ffffff',
    'text_dim': '#888888',
    'highlight': '#ff6b6b',  # Red for highlight
    'border': '#333366'
}

DATA_FILE = os.path.join(os.path.dirname(__file__), 'todos.json')


class TodoItem:
    """Data model for a single todo item."""
    def __init__(self, text, parent_id=None):
        self.id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.text = text
        self.completed = False
        self.highlighted = False
        self.created_at = datetime.now().isoformat()
        self.parent_id = parent_id
        self.notes = ""
        self.links = []  # List of {url, title}
        self.tags = []
        self.children = []  # Sub-items
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'completed': self.completed,
            'highlighted': self.highlighted,
            'created_at': self.created_at,
            'parent_id': self.parent_id,
            'notes': self.notes,
            'links': self.links,
            'tags': self.tags,
            'children': [c.to_dict() for c in self.children]
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(data['text'], data.get('parent_id'))
        item.id = data['id']
        item.completed = data.get('completed', False)
        item.highlighted = data.get('highlighted', False)
        item.created_at = data.get('created_at', datetime.now().isoformat())
        item.notes = data.get('notes', '')
        item.links = data.get('links', [])
        item.tags = data.get('tags', [])
        item.children = [cls.from_dict(c) for c in data.get('children', [])]
        return item


class QuickInputBox(QFrame):
    """One-click quick input for new todos."""
    submitted = pyqtSignal(str)
    expand_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 50)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("Quick add todo...")
        self.input.returnPressed.connect(self.submit)
        layout.addWidget(self.input)
        
        # Expand button
        self.expand_btn = QPushButton("⊞")
        self.expand_btn.setFixedSize(30, 30)
        self.expand_btn.clicked.connect(self.expand_requested.emit)
        layout.addWidget(self.expand_btn)
        
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['primary']};
                border-radius: 12px;
            }}
            QLineEdit {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
            }}
        """)
    
    def submit(self):
        text = self.input.text().strip()
        if text:
            self.submitted.emit(text)
            self.input.clear()


class TodoPanel(QFrame):
    """Full todo list panel - slide out, 1.5x hndl-it size."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 500)  # 1.5x larger
        self.todos = []
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📋 todo-it")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_dim']};
                font-size: 18px;
                border: none;
            }}
            QPushButton:hover {{ color: {COLORS['highlight']}; }}
        """)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Quick input
        input_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Add new todo...")
        self.input.returnPressed.connect(self.add_todo)
        input_layout.addWidget(self.input)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(30, 30)
        add_btn.clicked.connect(self.add_todo)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)
        
        # Tree widget for hierarchical todos
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(self.toggle_complete)
        self.tree.itemExpanded.connect(lambda: self.save_data())
        layout.addWidget(self.tree)
        
        # Notes/details panel (collapsible)
        self.details = QTextEdit()
        self.details.setPlaceholderText("Notes, links, details...")
        self.details.setMaximumHeight(100)
        self.details.hide()
        self.details.textChanged.connect(self.save_current_notes)
        layout.addWidget(self.details)
        
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['primary']};
                border-radius: 16px;
            }}
            QLineEdit {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
            }}
            QTreeWidget {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 5px;
            }}
            QTreeWidget::item {{
                padding: 6px;
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS['primary']}40;
            }}
            QTreeWidget::item:hover {{
                background-color: {COLORS['secondary']}20;
            }}
            QTextEdit {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
    
    def add_todo(self, text=None):
        if text is None:
            text = self.input.text().strip()
        if not text:
            return
            
        item = TodoItem(text)
        self.todos.append(item)
        self.add_tree_item(item)
        self.input.clear()
        self.save_data()
    
    def add_tree_item(self, todo_item, parent_widget=None):
        """Add a todo item to the tree."""
        widget = QTreeWidgetItem()
        widget.setData(0, Qt.ItemDataRole.UserRole, todo_item.id)
        self.update_item_display(widget, todo_item)
        
        if parent_widget:
            parent_widget.addChild(widget)
        else:
            self.tree.addTopLevelItem(widget)
        
        # Add children recursively
        for child in todo_item.children:
            self.add_tree_item(child, widget)
        
        return widget
    
    def update_item_display(self, widget, todo_item):
        """Update the visual display of a tree item."""
        prefix = "✓ " if todo_item.completed else "○ "
        widget.setText(0, prefix + todo_item.text)
        
        # Styling based on state
        if todo_item.completed:
            widget.setForeground(0, QBrush(QColor(COLORS['accent'])))
            font = widget.font(0)
            font.setStrikeOut(True)
            widget.setFont(0, font)
        elif todo_item.highlighted:
            widget.setForeground(0, QBrush(QColor(COLORS['highlight'])))
            font = widget.font(0)
            font.setBold(True)
            widget.setFont(0, font)
        else:
            widget.setForeground(0, QBrush(QColor(COLORS['text'])))
    
    def find_todo_by_id(self, todo_id, items=None):
        """Find a todo item by ID."""
        if items is None:
            items = self.todos
        for item in items:
            if item.id == todo_id:
                return item
            found = self.find_todo_by_id(todo_id, item.children)
            if found:
                return found
        return None
    
    def toggle_complete(self, widget, column):
        """Double-click to toggle completion."""
        todo_id = widget.data(0, Qt.ItemDataRole.UserRole)
        todo = self.find_todo_by_id(todo_id)
        if todo:
            todo.completed = not todo.completed
            self.update_item_display(widget, todo)
            self.save_data()
    
    def show_context_menu(self, pos):
        """Right-click context menu."""
        widget = self.tree.itemAt(pos)
        if not widget:
            return
            
        todo_id = widget.data(0, Qt.ItemDataRole.UserRole)
        todo = self.find_todo_by_id(todo_id)
        if not todo:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        # Actions
        complete_action = menu.addAction("✓ Complete" if not todo.completed else "↩ Uncomplete")
        highlight_action = menu.addAction("🔥 Highlight" if not todo.highlighted else "💨 Remove Highlight")
        menu.addSeparator()
        add_sub = menu.addAction("➕ Add Sub-task")
        add_link = menu.addAction("🔗 Add Link")
        add_note = menu.addAction("📝 Edit Notes")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete")
        
        action = menu.exec(self.tree.mapToGlobal(pos))
        
        if action == complete_action:
            todo.completed = not todo.completed
            self.update_item_display(widget, todo)
        elif action == highlight_action:
            todo.highlighted = not todo.highlighted
            self.update_item_display(widget, todo)
        elif action == add_sub:
            self.add_subtask(widget, todo)
        elif action == add_link:
            self.add_link_dialog(todo)
        elif action == add_note:
            self.show_notes(todo)
        elif action == delete_action:
            self.delete_todo(widget, todo)
        
        self.save_data()
    
    def add_subtask(self, parent_widget, parent_todo):
        """Add a sub-task."""
        # Quick inline add would be better, but for now just add a placeholder
        sub = TodoItem("New sub-task", parent_todo.id)
        parent_todo.children.append(sub)
        self.add_tree_item(sub, parent_widget)
        parent_widget.setExpanded(True)
        self.save_data()
    
    def add_link_dialog(self, todo):
        """TODO: Add link dialog."""
        # For now, just append to notes
        todo.notes += "\n[Link placeholder]"
        self.save_data()
    
    def show_notes(self, todo):
        """Show/hide notes panel for this item."""
        self.current_todo = todo
        self.details.setText(todo.notes)
        self.details.show()
    
    def save_current_notes(self):
        """Save notes from the details panel."""
        if hasattr(self, 'current_todo') and self.current_todo:
            self.current_todo.notes = self.details.toPlainText()
            self.save_data()
    
    def delete_todo(self, widget, todo):
        """Delete a todo item."""
        # Remove from data
        self.todos = [t for t in self.todos if t.id != todo.id]
        # Also check children
        for t in self.todos:
            t.children = [c for c in t.children if c.id != todo.id]
        
        # Remove from tree
        parent = widget.parent()
        if parent:
            parent.removeChild(widget)
        else:
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(widget))
        
        self.save_data()
    
    def save_data(self):
        """Save todos to JSON file."""
        data = [t.to_dict() for t in self.todos]
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_data(self):
        """Load todos from JSON file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                self.todos = [TodoItem.from_dict(d) for d in data]
                for todo in self.todos:
                    self.add_tree_item(todo)
            except Exception as e:
                print(f"Error loading todos: {e}")
    
    def show_animated(self):
        """Slide in animation."""
        self.show()
        # Could add QPropertyAnimation here for slide effect


class TodoItApp:
    """Main todo-it application controller."""
    
    def __init__(self):
        self.quick_input = QuickInputBox()
        self.panel = TodoPanel()
        
        # Wiring
        self.quick_input.submitted.connect(self.panel.add_todo)
        self.quick_input.expand_requested.connect(self.show_panel)
    
    def show_quick_input(self, x, y):
        """Show quick input at position."""
        self.quick_input.move(x, y)
        self.quick_input.show()
        self.quick_input.input.setFocus()
    
    def show_panel(self, x=None, y=None):
        """Show full panel."""
        if x and y:
            self.panel.move(x, y)
        self.panel.show_animated()
        self.quick_input.hide()


# Standalone test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    todo_app = TodoItApp()
    todo_app.panel.show()
    todo_app.panel.move(100, 100)
    
    sys.exit(app.exec())
