"""System tray icon with full menu."""
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication, QInputDialog
from PyQt5.QtGui     import QPixmap, QPainter, QPainterPath, QIcon, QColor
from PyQt5.QtCore    import Qt
import styles

def _icon():
    px = QPixmap(22, 22)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(1, 7, 20, 8, 4, 4)
    p.fillPath(path, QColor(styles.TEXT_PRIMARY))
    p.end()
    return QIcon(px)

class SystemTrayManager:
    def __init__(self, island, app):
        self.island = island
        self.app    = app
        self.tray   = QSystemTrayIcon()

    def setup(self):
        self.tray.setIcon(_icon())
        self.tray.setToolTip("Dynamic Island")

        menu = QMenu()
        menu.setStyleSheet(styles.CONTEXT_MENU_STYLE)

        def add(label, fn):
            a = QAction(label)
            a.triggered.connect(fn)
            menu.addAction(a)

        add("Anzeigen",       self.island.show)
        add("Einstellungen",  self.island.show_settings)
        menu.addSeparator()

        add("📝  Neue Notiz...",   self._new_note)
        add("📋  Zwischenablage", self._show_clipboard)
        menu.addSeparator()

        add("▶  Timer starten",   self.island.timer.start)
        add("⏸  Timer pausieren", self.island.timer.pause)
        add("⏹  Timer zurück",    self.island.timer.reset)
        menu.addSeparator()

        add("●  Mikrofon-Test",  lambda: self.island.push_event("●","Mikrofon aktiv","",styles.ACCENT_ORANGE,3000))
        add("●  Kamera-Test",    lambda: self.island.push_event("●","Kamera aktiv","",styles.ACCENT_GREEN,3000))
        menu.addSeparator()

        add("Beenden", self._quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.island.show() if r == QSystemTrayIcon.DoubleClick else None
        )
        self.tray.show()

    def _new_note(self):
        text, ok = QInputDialog.getText(None, "Neue Notiz", "Notiz eingeben:")
        if ok and text.strip():
            self.island.notes.add_note(text.strip())
            self.island.push_event("📝", "Notiz gespeichert", text[:22], styles.ACCENT_BLUE, 2000)

    def _show_clipboard(self):
        self.island.clipboard._set_active(True)
        self.island.go_expanded()

    def _quit(self):
        self.island.cleanup()
        self.tray.hide()
        self.app.quit()
