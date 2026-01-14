import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QScrollArea, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Import tools
from brand_it import BrandItTool

class ShedMenu(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        layout = QVBoxLayout(self)
        
        # Header
        lbl = QLabel("THE SHED")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #8888aa; margin-bottom: 10px;")
        layout.addWidget(lbl)
        
        # Grid of Tools (using VBox for now for simplicity)
        
        # Tool 1: Brand-it
        btn_brand = QPushButton("🏷️ Brand-it")
        btn_brand.setToolTip("The Namer. Create the perfect -it name.")
        btn_brand.setStyleSheet("""
            QPushButton {
                background-color: #2a2a3a;
                color: white;
                padding: 15px;
                text-align: left;
                font-size: 14px;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #3a3a4a; border-color: #00d4ff; }
        """)
        btn_brand.clicked.connect(lambda: self.switch_callback("brand_it"))
        layout.addWidget(btn_brand)
        
        # Tool 2: Ideas List
        btn_ideas = QPushButton("💡 The Pile")
        btn_ideas.setToolTip("The Heap. Ideas we haven't built yet.")
        btn_ideas.setStyleSheet("""
            QPushButton {
                background-color: #2a2a3a;
                color: #aaaaaa;
                padding: 15px;
                text-align: left;
                font-size: 14px;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #3a3a4a; border-color: #ffff00; }
        """)
        btn_ideas.clicked.connect(lambda: self.switch_callback("ideas"))
        layout.addWidget(btn_ideas)
        
        layout.addStretch()

class IdeasViewer(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.lbl = QLabel()
        self.lbl.setWordWrap(True)
        self.lbl.setStyleSheet("color: #cccccc; font-family: sans-serif;")
        self.lbl.setTextFormat(Qt.TextFormat.MarkdownText)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(self.lbl)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        layout.addWidget(scroll)
        
    def load_ideas(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "ideas.md")
            with open(path, "r") as f:
                content = f.read()
            self.lbl.setText(content)
        except Exception as e:
            self.lbl.setText(f"Could not load ideas: {e}")

class ShedItApp(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(350, 500)
        self.setWindowTitle("Shed-it")
        self.setStyleSheet("background-color: #121214;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Top Bar (Back button and Title)
        self.top_bar = QFrame()
        self.top_bar.setStyleSheet("background-color: #1a1a20; border-bottom: 1px solid #333;")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn_back = QPushButton("◀")
        self.btn_back.setFixedSize(30, 30)
        self.btn_back.clicked.connect(self.go_home)
        self.btn_back.setStyleSheet("color: white; background: transparent; font-weight: bold;")
        self.btn_back.hide() # Hidden on home
        
        self.lbl_title = QLabel("THE SHED")
        self.lbl_title.setStyleSheet("color: #666666; font-weight: bold;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        top_layout.addWidget(self.btn_back)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()
        # Spacer to balance back button
        dummy = QWidget() 
        dummy.setFixedSize(30, 30) 
        top_layout.addWidget(dummy)
        
        self.layout.addWidget(self.top_bar)
        
        # Stack
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # Pages
        self.menu_page = ShedMenu(self.switch_to_tool)
        self.brand_page = BrandItTool()
        self.ideas_page = IdeasViewer()
        
        self.stack.addWidget(self.menu_page)
        self.stack.addWidget(self.brand_page)
        self.stack.addWidget(self.ideas_page)
        
    def switch_to_tool(self, tool_name):
        if tool_name == "brand_it":
            self.stack.setCurrentWidget(self.brand_page)
            self.lbl_title.setText("BRAND-IT")
            self.btn_back.show()
        elif tool_name == "ideas":
            self.ideas_page.load_ideas()
            self.stack.setCurrentWidget(self.ideas_page)
            self.lbl_title.setText("THE PILE")
            self.btn_back.show()
            
    def go_home(self):
        self.stack.setCurrentWidget(self.menu_page)
        self.lbl_title.setText("THE SHED")
        self.btn_back.hide()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ShedItApp()
    window.show()
    sys.exit(app.exec())
