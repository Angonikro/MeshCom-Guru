import os
import sys

# Raspberry-Pi-sichere QtWebEngine-Einstellung.
# Unter Windows bleibt die vorhandene GPU/WebEngine-Konfiguration unangetastet.
if sys.platform.startswith("linux"):
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
