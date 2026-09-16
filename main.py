import os
import sys

# Raspberry-Pi-sichere QtWebEngine-Einstellung: GPU/Vulkan-Compositing
# wird nur für Chromium abgeschaltet. Qt Quick/RHI-Umgebungsvariablen werden
# bewusst NICHT gesetzt, weil sie auf älteren X11-Systemen selbst OpenGL-
# Initialisierungsfehler verursachen können.
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-gpu-compositing --disable-vulkan "
    "--disable-features=Vulkan,UseSkiaRenderer"
)

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
