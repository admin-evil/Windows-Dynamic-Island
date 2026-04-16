"""
Transient system event activity.

Auto-dismissing notifications shown briefly in the island:
  • Battery low / charging
  • Microphone active (orange dot)
  • Camera active (green dot)
  • Custom events

Battery state is polled every 60 seconds via psutil.
Other events can be pushed externally via push_event().
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore    import Qt, QTimer
from PyQt5.QtGui     import QFont

import styles
from activities.base import Activity

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

# Battery threshold for low-battery alert
BATTERY_LOW_PCT = 20


class TransientActivity(Activity):
    """
    Highest-priority activity (priority=1).
    Activates briefly when a system event fires, then self-dismisses.
    """
    priority = 1
    name     = "event"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._event: dict | None = None
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._dismiss)

        # Battery monitor
        self._last_battery: int | None = None
        self._last_plugged:  bool | None = None
        self._last_power_saver: bool | None = None
        if _PSUTIL:
            self._bat_timer = QTimer(self)
            self._bat_timer.timeout.connect(self._check_battery)
            self._bat_timer.start(60_000)
            QTimer.singleShot(3000, self._check_battery)  # initial check after 3s

    # ── Public API ────────────────────────────────────────────────────────────

    def push_event(self, icon: str, label: str, sub: str = "",
                   color: str = styles.ACCENT_BLUE, duration_ms: int = 3000):
        """Show a transient event for duration_ms milliseconds."""
        self._event = {"icon": icon, "label": label, "sub": sub, "color": color}
        self._dismiss_timer.stop()
        self._dismiss_timer.start(duration_ms)
        self._set_active(True)
        self.changed.emit()

    def push_mic_active(self):
        self.push_event("●", "Mikrofon aktiv", "", styles.ACCENT_ORANGE, 4000)

    def push_camera_active(self):
        self.push_event("●", "Kamera aktiv",   "", styles.ACCENT_GREEN, 4000)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _dismiss(self):
        self._event = None
        self._set_active(False)
        self.changed.emit()

    def _check_battery(self):
        if not _PSUTIL:
            return
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                return
            pct     = int(bat.percent)
            plugged = bat.power_plugged

            # Low battery alert
            if pct <= BATTERY_LOW_PCT and not plugged and self._last_battery != pct:
                self.push_event("🔋", f"Akku schwach – {pct}%",
                                "Bitte laden", styles.ACCENT_RED, 4000)

            # Just plugged in
            if plugged and self._last_plugged is False:
                self.push_event("⚡", f"Laden – {pct}%",
                                "", styles.ACCENT_GREEN, 2500)

            # Fully charged
            if pct >= 100 and plugged and self._last_battery != 100:
                self.push_event("✓", "Akku voll", "", styles.ACCENT_GREEN, 2500)

            # Power saver mode detection (energy saver threshold)
            power_saver = pct <= 20 and not plugged
            if power_saver and self._last_power_saver != power_saver:
                self.push_event("⚙️", "Energiesparmodus",
                                "Aktiviert", styles.ACCENT_ORANGE, 3000)
            elif not power_saver and self._last_power_saver is True:
                self.push_event("⚙️", "Energiesparmodus",
                                "Deaktiviert", styles.ACCENT_GREEN, 2500)

            self._last_battery = pct
            self._last_plugged  = plugged
            self._last_power_saver = power_saver
        except Exception:
            pass

    # ── Activity interface ────────────────────────────────────────────────────

    @property
    def live_data(self) -> dict:
        if not self._event:
            return {"icon": "!", "label": "", "sub": "", "color": styles.ACCENT_BLUE}
        return self._event

    def create_expanded_widget(self):
        # Transients don't have an expanded view
        w = QWidget()
        w.setAttribute(Qt.WA_TranslucentBackground)
        lbl = QLabel(self._event.get("label", "") if self._event else "")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {styles.TEXT_PRIMARY}; background: transparent;")
        l = QVBoxLayout(w)
        l.addWidget(lbl)
        return w
