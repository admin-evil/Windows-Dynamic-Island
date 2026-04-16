"""
Dynamic Island for Windows  –  v3
Entry point.

    pip install -r requirements.txt
    python main.py
"""
import sys, os

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING",   "1")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import Qt

from config  import Config
from island  import DynamicIsland
from tray    import SystemTrayManager


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Dynamic Island")
    app.setStyle("Fusion")

    config = Config()
    island = DynamicIsland(config)
    island.show()

    tray = SystemTrayManager(island, app)
    tray.setup()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
