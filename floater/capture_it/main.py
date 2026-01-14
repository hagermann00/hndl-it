import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QRubberBand, QFrame)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPainter, QPen, QScreen, QPixmap, QIcon

try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("⚠️ mss not installed, falling back to basic capture")

class SnippingWidget(QWidget):
    """
    Overlay for Region Selection (Crop & Drag).
    Fixes 'Black Screen' bug by capturing screen *before* showing overlay.
    """
    captured = pyqtSignal(QPixmap)
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # We don't use TranslucentBackground here because we draw the screenshot itself
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) 
        
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.start_pos = None
        self.current_pos = None
        self.full_screen_pixmap = None
        
    def start_selection(self):
        """Capture screen properly and show overlay"""
        # 1. Grab screen using MSS (fast & robust) or QScreen (fallback)
        # Hide self just in case
        self.hide()
        QApplication.processEvents()
        
        screen = QApplication.primaryScreen()
        geo = screen.geometry()
        
        # Capture logic
        if MSS_AVAILABLE:
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1] # 1 is primary
                sct_img = sct.grab(monitor)
                # Convert to QPixmap
                img = mss.tools.to_png(sct_img.rgb, sct_img.size)
                pixmap = QPixmap()
                pixmap.loadFromData(img)
                self.full_screen_pixmap = pixmap
        else:
            # Fallback
            self.full_screen_pixmap = screen.grabWindow(0)
            
        # 2. Resize to match screen
        self.setGeometry(geo)
        self.show()
        self.raise_()
        self.activateWindow()
        
    def paintEvent(self, event):
        if not self.full_screen_pixmap:
            return
            
        painter = QPainter(self)
        # Draw the frozen screen (background)
        painter.drawPixmap(0, 0, self.full_screen_pixmap)
        
        # Draw Dim Overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # Draw Selection (Clear Rect)
        if self.start_pos and self.current_pos:
            rect = QRect(self.start_pos, self.current_pos).normalized()
            # Draw the original pixels in the selection rect (undimmed)
            painter.drawPixmap(rect, self.full_screen_pixmap, rect)
            
            # Draw Border
            pen = QPen(QColor("#00d4ff"), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            
    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.current_pos = event.pos()
        self.update()
        
    def mouseMoveEvent(self, event):
        self.current_pos = event.pos()
        self.update()
        
    def mouseReleaseEvent(self, event):
        if self.start_pos and self.current_pos:
            rect = QRect(self.start_pos, self.current_pos).normalized()
            if rect.width() > 10 and rect.height() > 10:
                crop = self.full_screen_pixmap.copy(rect)
                self.captured.emit(crop)
            
        self.hide()

class CapturePanel(QWidget):
    """
    Panel with Camera (Full) and Scissors (Crop) buttons.
    """
    def __init__(self, icon_widget):
        super().__init__()
        self.icon_widget = icon_widget
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Content Frame (The visible part)
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        self.frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #1a1a1a;
                border: 2px solid #ff0000; /* Red Border for Camera */
                border-radius: 10px;
            }
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-size: 18px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #ff0000;
                color: white;
            }
        """)
        
        self.layout = QHBoxLayout(self.frame)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)
        
        self.main_layout.addWidget(self.frame)
        
        # Camera Button (Full Screen)
        self.btn_full = QPushButton("📷")
        self.btn_full.setToolTip("Full Screen Capture")
        self.btn_full.clicked.connect(self.capture_full)
        self.layout.addWidget(self.btn_full)
        
        # Scissors Button (Crop)
        self.btn_crop = QPushButton("✂️")
        self.btn_crop.setToolTip("Crop & Drag")
        self.btn_crop.clicked.connect(self.start_crop)
        self.layout.addWidget(self.btn_crop)
        
        self.snipper = SnippingWidget()
        self.snipper.captured.connect(self.on_captured)
        
        # Action Overlay
        self.action_overlay = None

        print("📸 CapturePanel initialized")

    def capture_full(self):
        """Capture full screen immediately"""
        print("📸 Full capture requested")
        self.hide()
        QTimer.singleShot(200, self.do_capture)
        
    def do_capture(self):
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0)
        self.save_capture(pixmap)
        
    def start_crop(self):
        """Start snipping tool"""
        print("✂️ Snipping requested")
        self.hide()
        # Delay to let menu fade
        QTimer.singleShot(200, self.snipper.start_selection)
        
    def on_captured(self, pixmap):
        print("✅ Image captured via Snipper")
        self.save_capture(pixmap)
        self.show_action_menu(pixmap)

    def show_action_menu(self, pixmap):
        """Show the post-capture action menu"""
        from floater.capture_it.action_overlay import ActionOverlay

        # Close existing if any
        if self.action_overlay:
            self.action_overlay.close()

        self.action_overlay = ActionOverlay(pixmap)
        self.action_overlay.action_selected.connect(self.handle_action)

        # Position near mouse
        cursor_pos = QPoint(QApplication.primaryScreen().cursor().pos())
        self.action_overlay.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.action_overlay.show()
        
    def handle_action(self, action, payload):
        """Handle action from overlay"""
        print(f"⚡ Action selected: {action}")

        if action == "save":
            # Already saved in on_captured, just feedback
            pass

        elif action in ["explain", "resale"]:
            # Send to Brain Agent via IPC
            try:
                from shared.ipc import send_command

                prompt = "Explain this image in detail."
                if action == "resale":
                    prompt = "Analyze this item for resale. Identify the product, estimate value, and suggest search terms for comps."

                send_command("brain", "analyze_image", {
                    "image": payload["image"],
                    "prompt": prompt
                })
                print(f"📨 Sent {action} request to Brain")

                # Show feedback
                # Ideally we show a 'thinking' toast or open the chat
                send_command("floater", "display", {
                    "type": "info",
                    "content": f"🧠 Brain is analyzing image for {action}..."
                })

            except Exception as e:
                print(f"❌ Failed to send IPC: {e}")

    def save_capture(self, pixmap):
        """Save capture to file and clipboard"""
        try:
            # 1. Save to Clipboard
            cb = QApplication.clipboard()
            cb.setPixmap(pixmap)
            print("📋 Copied to clipboard")
            
            # 2. Save to Disk (Inbox)
            # Use centralized registry for correct Inbox location
            try:
                from shared.module_registry import MODULES
                folder = MODULES["capture-it"]["inbox"]
            except ImportError:
                print("⚠️ shared.module_registry not found, falling back to desktop")
                folder = os.path.join(os.path.expanduser("~"), "Desktop")
            except KeyError:
                print("⚠️ capture-it not in registry, falling back to desktop")
                folder = os.path.join(os.path.expanduser("~"), "Desktop")

            # Ensure folder exists
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                except Exception as e:
                    print(f"❌ Failed to create inbox folder {folder}: {e}")
                    folder = os.path.join(os.path.expanduser("~"), "Desktop")

            import datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{ts}.png"
            path = os.path.join(folder, filename)
            
            pixmap.save(path)
            print(f"✅ Capture saved to {path}")
            
            # Show feedback (optional)
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
