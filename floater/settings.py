import logging
import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTabWidget, QWidget, QListWidget, 
    QTextEdit, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from floater.config import ConfigManager

logger = logging.getLogger("hndl-it.floater.settings")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hndl-it Settings")
        self.resize(600, 450)
        self.config = ConfigManager()
        
        # Layouts
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: General (Model Selection)
        self.tab_general = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.tab_general, "General / AI")
        
        # Tab 2: Memory (Saved Tasks)
        self.tab_memory = QWidget()
        self.setup_memory_tab()
        self.tabs.addTab(self.tab_memory, "Memory / Workflows")
        
        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save & Close")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        # Load Data
        self.load_data()

    def setup_general_tab(self):
        layout = QFormLayout(self.tab_general)
        
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("http://localhost:11434")
        layout.addRow("Ollama API URL:", self.input_url)
        
        btn_refresh = QPushButton("Refresh Models")
        btn_refresh.clicked.connect(self.refresh_models)
        layout.addRow("", btn_refresh)
        
        self.combo_model = QComboBox()
        layout.addRow("Active Model:", self.combo_model)
        
        # Info
        lbl_info = QLabel("Select the local LLM to use for task planning and routing.\nRequires Ollama running locally.")
        lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addRow("", lbl_info)

    def setup_memory_tab(self):
        layout = QHBoxLayout(self.tab_memory)
        
        # Left: List
        left_layout = QVBoxLayout()
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.on_task_selected)
        left_layout.addWidget(QLabel("Saved Tasks:"))
        left_layout.addWidget(self.task_list)
        
        btn_new = QPushButton("New Task")
        btn_new.clicked.connect(self.on_new_task)
        left_layout.addWidget(btn_new)
        
        layout.addLayout(left_layout, 1)
        
        # Right: Editor
        right_group = QGroupBox("Task Details")
        right_layout = QVBoxLayout(right_group)
        
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Task Name")
        right_layout.addWidget(QLabel("Name:"))
        right_layout.addWidget(self.edit_name)
        
        self.edit_commands = QTextEdit()
        self.edit_commands.setPlaceholderText("Enter commands (one per line)\nExample:\nopen google.com\nclick #search")
        right_layout.addWidget(QLabel("Commands:"))
        right_layout.addWidget(self.edit_commands)
        
        btn_row = QHBoxLayout()
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet("background-color: #552222;")
        btn_delete.clicked.connect(self.delete_task)
        
        btn_save_task = QPushButton("Save Task")
        btn_save_task.setStyleSheet("background-color: #225522;")
        btn_save_task.clicked.connect(self.save_current_task)
        
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_save_task)
        right_layout.addLayout(btn_row)
        
        layout.addWidget(right_group, 2)
        
        self.current_task_id = None

    def load_data(self):
        # General
        url = self.config.get("ollama_url")
        self.input_url.setText(url)
        
        # Try to load models if we have them cached or just let user refresh
        # We'll just populate current selection if it exists
        current_model = self.config.get("active_model")
        if current_model:
            self.combo_model.addItem(current_model)
            self.combo_model.setCurrentText(current_model)
            
        # Memory
        self.refresh_task_list()

    def refresh_models(self):
        url = self.input_url.text().strip()
        if not url: return
        
        try:
            # Clean URL
            if not url.startswith("http"):
                url = "http://" + url
                self.input_url.setText(url)
                
            api_endpoint = f"{url}/api/tags"
            logger.info(f"Fetching models from {api_endpoint}")
            
            resp = requests.get(api_endpoint, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                
                self.combo_model.clear()
                self.combo_model.addItems(models)
                
                # Restore previous selection if possible
                current = self.config.get("active_model")
                if current in models:
                    self.combo_model.setCurrentText(current)
                    
                QMessageBox.information(self, "Success", f"Found {len(models)} models.")
            else:
                QMessageBox.warning(self, "Error", f"Ollama returned {resp.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            QMessageBox.critical(self, "Connection Error", f"Could not connect to Ollama:\n{e}")

    # Memory Logic
    def refresh_task_list(self):
        self.task_list.clear()
        tasks = self.config.get_tasks()
        for t in tasks:
            self.task_list.addItem(t["name"])
    
    def on_task_selected(self, item):
        name = item.text()
        tasks = self.config.get_tasks()
        task = next((t for t in tasks if t["name"] == name), None)
        if task:
            self.current_task_id = task["id"]
            self.edit_name.setText(task["name"])
            self.edit_commands.setText("\n".join(task["commands"]))
            
    def on_new_task(self):
        self.current_task_id = None
        self.edit_name.clear()
        self.edit_commands.clear()
        self.task_list.clearSelection()
        self.edit_name.setFocus()

    def save_current_task(self):
        name = self.edit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Task Name is required.")
            return
            
        commands = [
            line.strip() 
            for line in self.edit_commands.toPlainText().split('\n') 
            if line.strip()
        ]
        
        if self.current_task_id:
            # Update
            tasks = self.config.get_tasks()
            for t in tasks:
                if t["id"] == self.current_task_id:
                    t["name"] = name
                    t["commands"] = commands
                    break
            self.config.set("saved_tasks", tasks)
        else:
            # Create
            self.config.add_task(name, commands)
            
        self.refresh_task_list()
        # Reselect
        items = self.task_list.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.task_list.setCurrentItem(items[0])
            # Re-fetch ID if it was new
            if not self.current_task_id:
                 tasks = self.config.get_tasks()
                 task = next((t for t in tasks if t["name"] == name), None)
                 if task: self.current_task_id = task["id"]

    def delete_task(self):
        if not self.current_task_id: return
        
        res = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this task?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if res == QMessageBox.StandardButton.Yes:
            self.config.remove_task(self.current_task_id)
            self.on_new_task() # Clear form
            self.refresh_task_list()

    def accept(self):
        # Save General Settings on Close
        self.config.set("ollama_url", self.input_url.text().strip())
        self.config.set("active_model", self.combo_model.currentText())
        super().accept()
