"""
Timer / Stopwatch activity.
Supports countdown (Pomodoro-style) and stopwatch mode.
Highest self-managed priority among user activities.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QFont, QPainter, QPainterPath, QColor

import styles
from activities.base import Activity

POMODORO_SECS = 25 * 60


class TimerActivity(Activity):
    priority = 3
    name     = "timer"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode     = "stopwatch"   # "stopwatch" | "countdown"
        self._elapsed  = 0            # seconds elapsed
        self._target   = POMODORO_SECS
        self._running  = False

        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._on_tick)

    # ── Playback ──────────────────────────────────────────────────────────────

    def start(self):
        if not self._running:
            self._running = True
            self._tick.start()
            self._set_active(True)
            self.changed.emit()

    def pause(self):
        if self._running:
            self._running = False
            self._tick.stop()
            self.changed.emit()

    def reset(self):
        self._running = False
        self._tick.stop()
        self._elapsed = 0
        self._set_active(False)
        self.changed.emit()

    def set_mode(self, mode: str):
        self.reset()
        self._mode = mode

    def set_countdown_secs(self, secs: int):
        self._target  = max(1, secs)
        self._elapsed = 0
        self.changed.emit()

    def _on_tick(self):
        if self._mode == "stopwatch":
            self._elapsed += 1
        else:
            self._elapsed += 1
            if self._elapsed >= self._target:
                self._elapsed = self._target
                self.pause()
        self.changed.emit()

    # ── Data ──────────────────────────────────────────────────────────────────

    @property
    def display_str(self) -> str:
        secs = self._remaining if self._mode == "countdown" else self._elapsed
        h, r = divmod(abs(secs), 3600)
        m, s = divmod(r, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @property
    def _remaining(self) -> int:
        return max(0, self._target - self._elapsed)

    @property
    def progress(self) -> float:
        if self._mode == "stopwatch" or self._target == 0:
            return 0.0
        return min(1.0, self._elapsed / self._target)

    @property
    def running(self) -> bool:
        return self._running

    @property
    def live_data(self) -> dict:
        icon = "⏱" if self._mode == "stopwatch" else "⏳"
        return {
            "icon":     icon,
            "label":    self.display_str,
            "sub":      "Läuft" if self._running else "Pausiert",
            "color":    styles.ACCENT_ORANGE,
            "progress": self.progress,
        }

    def create_expanded_widget(self):
        return _TimerExpandedWidget(self)


# ── Expanded widget ───────────────────────────────────────────────────────────

class _TimerExpandedWidget(QWidget):
    def __init__(self, activity: TimerActivity, parent=None):
        super().__init__(parent)
        self._act = activity
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()
        activity.changed.connect(self._refresh)
        self._refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Mode switch row
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        self.sw_btn  = _PillToggle("Stopwatch")
        self.cd_btn  = _PillToggle("Countdown")
        self.sw_btn.clicked.connect(lambda: self._switch_mode("stopwatch"))
        self.cd_btn.clicked.connect(lambda: self._switch_mode("countdown"))
        mode_row.addStretch()
        mode_row.addWidget(self.sw_btn)
        mode_row.addWidget(self.cd_btn)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Big time display
        self.time_lbl = QLabel("00:00")
        tf = QFont(styles.FONT_FAMILY, 48)
        tf.setWeight(QFont.Thin)
        tf.setLetterSpacing(QFont.AbsoluteSpacing, -2)
        self.time_lbl.setFont(tf)
        self.time_lbl.setStyleSheet(
            f"color: {styles.TEXT_PRIMARY}; background: transparent;"
        )
        self.time_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_lbl)

        # Progress ring (countdown only)
        self.ring = _ProgressRing(styles.ACCENT_ORANGE)
        self.ring.setVisible(False)
        layout.addWidget(self.ring, 0, Qt.AlignHCenter)

        # Set time row (countdown only)
        self.set_row = QWidget()
        set_layout   = QHBoxLayout(self.set_row)
        set_layout.setContentsMargins(0, 0, 0, 0)
        set_layout.setSpacing(6)

        self.min_spin = _NumSpin(59, "min")
        self.sec_spin = _NumSpin(59, "sec")
        self.set_row.setVisible(False)

        set_layout.addStretch()
        set_layout.addWidget(self.min_spin)
        set_layout.addWidget(self.sec_spin)
        set_layout.addStretch()
        layout.addWidget(self.set_row)

        # Control buttons
        ctrl = QHBoxLayout()
        ctrl.setSpacing(16)
        ctrl.setContentsMargins(0, 0, 0, 0)

        self.start_btn = _CtrlBtn("Start",  styles.ACCENT_GREEN)
        self.reset_btn = _CtrlBtn("Reset",  styles.TEXT_TERTIARY)

        self.start_btn.clicked.connect(self._toggle)
        self.reset_btn.clicked.connect(self._act.reset)

        ctrl.addStretch()
        ctrl.addWidget(self.start_btn)
        ctrl.addWidget(self.reset_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

    def _switch_mode(self, mode: str):
        self._act.set_mode(mode)
        self._refresh()

    def _toggle(self):
        if self._act.running:
            self._act.pause()
        else:
            if self._act._mode == "countdown":
                secs = self.min_spin.value() * 60 + self.sec_spin.value()
                self._act.set_countdown_secs(secs)
            self._act.start()

    def _refresh(self):
        mode = self._act._mode
        self.sw_btn.set_active(mode == "stopwatch")
        self.cd_btn.set_active(mode == "countdown")
        self.ring.setVisible(mode == "countdown" and self._act.is_active)
        self.set_row.setVisible(mode == "countdown" and not self._act.running)

        self.time_lbl.setText(self._act.display_str)

        if mode == "countdown":
            self.ring.set_value(self._act.progress)
            self.time_lbl.setStyleSheet(
                f"color: {styles.ACCENT_ORANGE}; background: transparent;"
            )
        else:
            self.time_lbl.setStyleSheet(
                f"color: {styles.TEXT_PRIMARY}; background: transparent;"
            )

        self.start_btn.set_label("Pause" if self._act.running else "Start")
        self.start_btn.set_color(styles.ACCENT_RED if self._act.running else styles.ACCENT_GREEN)


# ── Sub-widgets ───────────────────────────────────────────────────────────────

class _ProgressRing(QWidget):
    SIZE = 56

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self._v     = 0.0
        self._color = QColor(color)

    def set_value(self, v: float):
        self._v = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, _):
        from PyQt5.QtGui import QPen
        from PyQt5.QtCore import QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = p.pen()
        # Track
        pen.setWidth(4)
        pen.setColor(QColor(styles.BG_ELEVATED))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawEllipse(4, 4, self.SIZE-8, self.SIZE-8)
        # Fill
        pen.setColor(self._color)
        p.setPen(pen)
        span = -int(360 * 16 * self._v)  # Qt uses 1/16 degree units
        p.drawArc(QRectF(4, 4, self.SIZE-8, self.SIZE-8), 90*16, span)


class _PillToggle(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._on = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(26)
        self._apply()

    def set_active(self, flag: bool):
        self._on = flag
        self._apply()

    def _apply(self):
        bg = styles.ACCENT_ORANGE if self._on else "rgba(255,255,255,0.06)"
        fg = "white" if self._on else styles.TEXT_SECONDARY
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: none;
                border-radius: 13px;
                padding: 0 14px;
                font-size: 11px;
                font-family: {styles.FONT_FAMILY};
                font-weight: 500;
            }}
        """)


class _NumSpin(QSpinBox):
    def __init__(self, max_val: int, suffix: str, parent=None):
        super().__init__(parent)
        self.setRange(0, max_val)
        self.setValue(5 if suffix == "min" else 0)
        self.setSuffix(f" {suffix}")
        self.setFixedWidth(72)
        self.setStyleSheet(f"""
            QSpinBox {{
                background: {styles.BG_ELEVATED};
                color: {styles.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 4px 8px;
                font-family: {styles.FONT_FAMILY};
                font-size: 12px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0;
            }}
        """)


class _CtrlBtn(QPushButton):
    def __init__(self, label: str, color: str, parent=None):
        super().__init__(label, parent)
        self._color = color
        self.setFixedSize(90, 36)
        self.setCursor(Qt.PointingHandCursor)
        self._apply()

    def set_label(self, text: str):
        self.setText(text)

    def set_color(self, color: str):
        self._color = color
        self._apply()

    def _apply(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self._color};
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 13px;
                font-family: {styles.FONT_FAMILY};
                font-weight: 500;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton:pressed {{ opacity: 0.70; }}
        """)
