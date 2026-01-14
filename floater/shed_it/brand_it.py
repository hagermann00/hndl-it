from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPlainTextEdit, QPushButton, QApplication, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QClipboard

class BrandItTool(QWidget):
    """
    The 'Brand-it' Tool.
    Generates the perfect prompting strategy to name your next Antigravity tool.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # header
        self.header = QLabel("THE BRAND-IT")
        self.header.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 16px;")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.header)
        
        # Description Input
        self.lbl_input = QLabel("What does the thing do?")
        self.lbl_input.setStyleSheet("color: #aaaaaa;")
        self.layout.addWidget(self.lbl_input)
        
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("e.g. It creates a backup of all my files every hour...")
        self.input_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e2e;
                color: #ffffff;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.input_edit.setFixedHeight(80)
        self.layout.addWidget(self.input_edit)
        
        # Action Button
        self.btn_generate = QPushButton("Forge the Prompt")
        self.btn_generate.setFixedHeight(40)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #33e0ff;
            }
        """)
        self.btn_generate.clicked.connect(self.generate_prompt)
        self.layout.addWidget(self.btn_generate)
        
        # Output Area
        self.lbl_output = QLabel("Copy this to your LLM:")
        self.lbl_output.setStyleSheet("color: #aaaaaa;")
        self.layout.addWidget(self.lbl_output)
        
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111116;
                color: #00ff88;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        self.layout.addWidget(self.output_edit)
        
        # Copy Button
        self.btn_copy = QPushButton("Copy to Clipboard")
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #2a2a3a;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3a3a4a;
            }
        """)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.layout.addWidget(self.btn_copy)
        
    def generate_prompt(self):
        desc = self.input_edit.toPlainText().strip()
        if not desc:
            self.output_edit.setPlainText("Wait, you didn't tell me what the thing does.")
            return
            
        prompt = f"""
You are the Lead Brand Architect for 'Antigravity', a suite of hyper-utilitarian, slightly snarky developer tools.

TASK:
Name a new tool based on the description provided below.

BRANDING GUIDELINES:
1. FORMAT: [ShortVerb/Noun][VowelReduction]-it
   - Examples: 'prnt-it', 'scl-it', 'run-it', 'grab-it'
   - Maximum 4 letters before the hyphen if possible. 3 is better.
   - Vowels are expensive. Drop them if the word is still readable (e.g. 'scal' -> 'scl').

2. TAGLINE: "The [Noun]. [Dry, quaint observation about the utility]."
   - Example for a color picker: "The Snatch. Steals colors from pixels when you aren't looking."
   - Example for a resizer: "The Scale. Shrinks your jpegs without shrinking their soul."

3. PERSONALITY:
   - Utilitarian, Cyberpunk-lite, Dry Humor.
   - No "Super Awesome Tool". Keep it grounded.

USER DESCRIPTION OF TOOL:
"{desc}"

OUTPUT FORMAT:
Provide 5 creative options in this format:
1. `[name-it]` : [The Noun]. [The Tagline].
"""
        self.output_edit.setPlainText(prompt.strip())
        
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_edit.toPlainText())
        self.btn_copy.setText("Copied!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.btn_copy.setText("Copy to Clipboard"))

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = BrandItTool()
    window.show()
    sys.exit(app.exec())
