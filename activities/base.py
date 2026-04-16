"""
Base class for all Dynamic Island activities.

An Activity represents something the system is doing that
deserves a presence in the island. Examples: music, timer, call.

Priority (lower = more important):
    0  Active phone/video call
    1  System alert (low battery, privacy warning)
    2  Navigation
    3  Timer/countdown
    4  Music/media
    5  Other
"""
from PyQt5.QtCore import QObject, pyqtSignal


class Activity(QObject):
    """
    Abstract base. Subclasses must implement:
        - priority (class attribute)
        - live_data property → dict with 'left' and optionally 'right' keys
        - create_expanded_widget() → QWidget
    """

    changed = pyqtSignal()      # emitted whenever content updates
    started = pyqtSignal()      # emitted when activity becomes active
    stopped = pyqtSignal()      # emitted when activity becomes inactive

    priority: int = 99
    name:     str = "base"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False

    # ── Active state ──────────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        return self._active

    def _set_active(self, flag: bool):
        if flag == self._active:
            return
        self._active = flag
        if flag:
            self.started.emit()
        else:
            self.stopped.emit()
        self.changed.emit()

    # ── Content ───────────────────────────────────────────────────────────────

    @property
    def live_data(self) -> dict:
        """
        Data for the compact Live Activity pill.

        Required keys:
            icon   str   – single Unicode char used as icon
            label  str   – main text (short!)
            sub    str   – secondary text (even shorter)
            color  str   – hex accent color for this activity

        Optional:
            progress float 0.0–1.0  – for a thin progress line
        """
        return {"icon": "?", "label": "Activity", "sub": "", "color": "#0A84FF"}

    def create_expanded_widget(self):
        """Returns a QWidget shown in the expanded panel. Override in subclass."""
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtCore    import Qt
        lbl = QLabel("(no expanded view)")
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def stop(self):
        """Called when the app is quitting. Clean up threads etc."""
        pass
