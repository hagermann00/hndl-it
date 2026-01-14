from PyQt6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
screen = app.primaryScreen()
rect = screen.geometry()
available = screen.availableGeometry()

print(f"Primary Screen: {rect.width()}x{rect.height()}")
print(f"Available Geometry: {available.x()},{available.y()} {available.width()}x{available.height()}")

# Check launch_suite logic
RIGHT_X = rect.width() - 80
print(f"Calculated RIGHT_X (Screen Width - 80): {RIGHT_X}")
