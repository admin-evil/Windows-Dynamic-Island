"""
Dynamic Island for Windows
Entry point.

    pip install -r requirements.txt
    python main.py
"""
import sys, os

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING",   "1")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import Qt

from version import __version__
from config  import Config
from island  import DynamicIsland
from tray    import SystemTrayManager
from updater import UpdateChecker, show_update_dialog


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(f"Dynamic Island v{__version__}")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")

    config = Config()
    island = DynamicIsland(config)
    island.show()

    tray = SystemTrayManager(island, app)
    tray.setup()

    # Start update checker in background
    updater = UpdateChecker()
    updater.update_available.connect(
        lambda new_ver, dl_url: show_update_dialog(island, new_ver, dl_url)
    )
    updater.check_for_updates()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
