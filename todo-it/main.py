"""
todo-it: Smart Todo List Module for hndl-it
Features:
- Slide-out panel (1.5x hndl-it size)
- Items with check/remove/highlight/expand (Relational Model)
- Sub-notes + links
- One-click input
"""

import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QFrame, QLabel, QMenu,
    QTextEdit, QSplitter, QApplication, QDialog, QDialogButtonBox, QFormLayout
    QTreeView, QFrame, QLabel, QMenu, QTextEdit, QTextBrowser, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QColor, QFont

# Import new model
from todo_model import TodoModel

# Colors matching hndl-it theme
COLORS = {
    'bg_dark': '#0a0a0a',
    'bg_panel': '#111111',
    'primary': '#00ff88',
    'secondary': '#00d4ff',
    'accent': '#00ff88',
    'text': '#ffffff',
    'text_dim': '#888888',
    'highlight': '#ff00ff',
    'border': '#1a1a1a'
}


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


class AddLinkDialog(QDialog):
    """Dialog to add a URL link with a title."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Link")
        self.setModal(True)

        layout = QFormLayout(self)
        self.url_input = QLineEdit()
        self.title_input = QLineEdit()
        layout.addRow("URL:", self.url_input)
        layout.addRow("Title:", self.title_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
            }}
            QLineEdit {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
            }}
        """)

    def get_data(self):
        return {
            'url': self.url_input.text().strip(),
            'title': self.title_input.text().strip()
        }


class TodoPanel(QFrame):
    """Full todo list panel - Relational View."""
    
    def __init__(self, model_file, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 500)
        
        self.model = TodoModel(model_file)
        self.init_ui()
        
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
        
        # Tree View (Model Based)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setExpandsOnDoubleClick(False) # We want double click to complete
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.doubleClicked.connect(self.toggle_complete)
        layout.addWidget(self.tree)
        
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
            QTreeView {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 5px;
            }}
            QTreeView::item {{
                padding: 6px;
                border-radius: 4px;
            }}
            QTreeView::item:selected {{
                background-color: {COLORS['primary']}40;
                color: {COLORS['text']}; 
            }}
            QTreeView::item:hover {{
                background-color: {COLORS['secondary']}20;
            }}
        """)
    
    def add_todo(self, text=None):
        if text is None:
            text = self.input.text().strip()
        if not text:
            return
            
        # Add to root (or selected?)
        # For quick input, usually root.
        self.model.add_item(text)
        self.input.clear()
        
    def toggle_complete(self, index):
        self.model.toggle_completion(index)
        
    def show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
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
        # Need to check state from model
        node = index.internalPointer()
        is_completed = node.data.get('status') == 'completed'
        
        complete_action = menu.addAction("✓ Complete" if not is_completed else "↩ Uncomplete")
        menu.addSeparator()
        add_sub = menu.addAction("➕ Add Sub-task")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete")
        
        action = menu.exec(self.tree.mapToGlobal(pos))
        
        if action == complete_action:
            self.model.toggle_completion(index)
        elif action == add_sub:
            self.model.add_item("New sub-task", index)
            self.tree.expand(index)
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
        """Show dialog to add a link."""
        dialog = AddLinkDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data['url']:
                # If no title is given, use the URL as the title
                if not data['title']:
                    data['title'] = data['url']
                todo.links.append(data)
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
    
            self.model.delete_item(index)
            
    def show_animated(self):
        self.show()

class TodoItApp:
    """Main todo-it application controller."""
    
    def __init__(self):
        # Point to the v2 file
        self.data_file = os.path.join(os.path.dirname(__file__), 'todos.json')
        # If v2 exists, use it? Or rename it?
        # Let's assume migration happened and we use todos_v2.json for now for safety, or todos.json if standardized.
        # Plan was to migrate and verify. Since we did that, we should point to the new structure.
        # However, the user might expect 'todos.json'.
        # Let's check if we want to use 'todos_v2.json' or overwrite.
        # For this refactor, let's use 'todos_v2.json' to be safe, then rename via script if desired.
        
        v2_path = os.path.join(os.path.dirname(__file__), 'todos_v2.json')
        if os.path.exists(v2_path):
            self.data_file = v2_path
            
        self.quick_input = QuickInputBox()
        self.panel = TodoPanel(self.data_file)
        
        # Wiring
        self.quick_input.submitted.connect(self.panel.add_todo)
        self.quick_input.expand_requested.connect(self.show_panel)
        
        # IPC Listener
        from PyQt6.QtCore import QTimer
        self.ipc_timer = QTimer()
        self.ipc_timer.timeout.connect(self.check_ipc)
        self.ipc_timer.start(1000)
        
    def check_ipc(self):
        try:
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.append(project_root)
                
            from shared.ipc import check_mailbox
            action, payload = check_mailbox("todo")
            if action:
                if action == "add_todo":
                    text = payload.get("text")
                    if text:
                        self.panel.add_todo(text)
                        self.panel.show_animated()
        except ImportError:
            pass
    
    def show_quick_input(self, x, y):
        self.quick_input.move(x, y)
        self.quick_input.show()
        self.quick_input.input.setFocus()
    
    def show_panel(self, x=None, y=None):
        if x and y:
            self.panel.move(x, y)
        self.panel.show_animated()
        self.quick_input.hide()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--y", type=int, default=450)
    args, _ = parser.parse_known_args()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    todo_app = TodoItApp()
    
    # Floating Icon logic (Simplified for testing)
    try:
        from overlay import TodoOverlay
        icon = TodoOverlay()
        screen_geo = app.primaryScreen().availableGeometry()
        x = screen_geo.width() - 80
        icon.move(x, args.y)
        icon.show()
        icon.clicked.connect(todo_app.panel.show_animated)
        icon.double_clicked.connect(todo_app.panel.show_animated)
    except ImportError:
        todo_app.panel.show()
    
    sys.exit(app.exec())
