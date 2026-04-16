"""
Music / Media activity.

Polls the Windows Global System Media Transport Controls every 2.5 s.
Works with Spotify, browsers, Apple Music, Windows Media Player.
Controls playback via virtual media keys (no extra libraries).
"""
import ctypes
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui  import QFont, QColor, QPainter, QPainterPath

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import styles
from activities.base import Activity
from utils.media     import get_current_media

# ── Virtual media keys (Windows) ──────────────────────────────────────────────
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT       = 0xB0
VK_MEDIA_PREV       = 0xB1


def _media_key(vk: int):
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk, 0, 0x0002, 0)
        except Exception:
            pass


# ── Background poller ─────────────────────────────────────────────────────────

class _Poller(QThread):
    result = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._run = True

    def run(self):
        while self._run:
            try:
                info = get_current_media()
            except Exception:
                info = None
            self.result.emit(info)
            self.msleep(2500)

    def stop(self):
        self._run = False
        self.quit()
        self.wait(4000)


# ── Activity ──────────────────────────────────────────────────────────────────

class MusicActivity(Activity):
    priority = 4
    name     = "music"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._info: dict | None = None
        self._poller = _Poller()
        self._poller.result.connect(self._on_result)
        self._poller.start()

    def _on_result(self, info):
        self._info = info
        self._set_active(bool(info and (info.get("is_playing") or info.get("title"))))
        self.changed.emit()

    @property
    def info(self) -> dict | None:
        return self._info

    @property
    def live_data(self) -> dict:
        if not self._info:
            return {"icon": "♫", "label": "Keine Wiedergabe", "sub": "", "color": styles.ACCENT_GREEN}
        title  = _trunc(self._info.get("title",  ""), 22)
        artist = _trunc(self._info.get("artist", ""), 18)
        playing = self._info.get("is_playing", False)
        return {
            "icon":    "♫",
            "label":   title or "Unbekannt",
            "sub":     artist,
            "color":   styles.ACCENT_GREEN,
            "playing": playing,
        }

    def create_expanded_widget(self):
        return _MusicExpandedWidget(self)

    def stop(self):
        self._poller.stop()


# ── Expanded widget ───────────────────────────────────────────────────────────

class _MusicExpandedWidget(QWidget):
    def __init__(self, activity: MusicActivity, parent=None):
        super().__init__(parent)
        self._act = activity
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()
        activity.changed.connect(self._refresh)
        self._refresh()

        # Fake progress that ticks
        self._progress_val = 0.0
        self._prog_timer = QTimer(self)
        self._prog_timer.timeout.connect(self._tick_progress)
        self._prog_timer.start(1000)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Album art placeholder
        self.art = _AlbumArt()
        layout.addWidget(self.art, 0, Qt.AlignHCenter)

        # Title
        self.title_lbl = QLabel("")
        tf = QFont(styles.FONT_FAMILY, 15)
        tf.setWeight(QFont.Medium)
        self.title_lbl.setFont(tf)
        self.title_lbl.setStyleSheet(f"color: {styles.TEXT_PRIMARY}; background: transparent;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)

        # Artist
        self.artist_lbl = QLabel("")
        af = QFont(styles.FONT_FAMILY, 12)
        af.setWeight(QFont.Normal)
        self.artist_lbl.setFont(af)
        self.artist_lbl.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; background: transparent;")
        self.artist_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.artist_lbl)

        # Progress bar
        self.prog = _SlimProgress()
        layout.addWidget(self.prog)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(24)
        ctrl.setContentsMargins(0, 4, 0, 0)

        self.prev_btn  = _CtrlBtn("⏮")
        self.play_btn  = _CtrlBtn("⏸", large=True)
        self.next_btn  = _CtrlBtn("⏭")

        self.prev_btn.clicked.connect(lambda: _media_key(VK_MEDIA_PREV))
        self.play_btn.clicked.connect(lambda: _media_key(VK_MEDIA_PLAY_PAUSE))
        self.next_btn.clicked.connect(lambda: _media_key(VK_MEDIA_NEXT))

        ctrl.addStretch()
        ctrl.addWidget(self.prev_btn)
        ctrl.addWidget(self.play_btn)
        ctrl.addWidget(self.next_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

    def _refresh(self):
        info = self._act.info
        if not info:
            self.title_lbl.setText("Keine Wiedergabe")
            self.artist_lbl.setText("")
            self.play_btn.setText("▶")
            return
        self.title_lbl.setText(info.get("title", ""))
        self.artist_lbl.setText(info.get("artist", ""))
        playing = info.get("is_playing", False)
        self.play_btn.setText("⏸" if playing else "▶")
        if playing and not self._prog_timer.isActive():
            self._prog_timer.start(1000)
        elif not playing:
            self._prog_timer.stop()

    def _tick_progress(self):
        info = self._act.info
        if info and info.get("is_playing"):
            self._progress_val = min(1.0, self._progress_val + 0.003)
            if self._progress_val >= 1.0:
                self._progress_val = 0.0
        self.prog.set_value(self._progress_val)


class _AlbumArt(QWidget):
    """Placeholder album art square with animated gradient."""
    SIZE = 72

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.SIZE, self.SIZE, 12, 12)
        p.setClipPath(path)
        # Gradient fill
        from PyQt5.QtGui import QLinearGradient
        g = QLinearGradient(0, 0, self.SIZE, self.SIZE)
        g.setColorAt(0, QColor("#1C1C2E"))
        g.setColorAt(1, QColor("#2C2C4E"))
        p.fillRect(0, 0, self.SIZE, self.SIZE, g)
        # Music note
        p.setPen(QColor(styles.TEXT_TERTIARY))
        f = QFont(styles.FONT_FAMILY, 22)
        p.setFont(f)
        p.drawText(0, 0, self.SIZE, self.SIZE, Qt.AlignCenter, "♫")


class _SlimProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._v = 0.0
        self.setFixedHeight(3)

    def set_value(self, v: float):
        self._v = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h, r = self.width(), self.height(), 1.5
        track = QPainterPath()
        track.addRoundedRect(0, 0, w, h, r, r)
        p.fillPath(track, QColor(styles.BG_ELEVATED))
        fw = int(w * self._v)
        if fw > 4:
            fill = QPainterPath()
            fill.addRoundedRect(0, 0, fw, h, r, r)
            p.fillPath(fill, QColor(styles.ACCENT_GREEN))


class _CtrlBtn(QPushButton):
    def __init__(self, text: str, large: bool = False, parent=None):
        super().__init__(text, parent)
        size = 46 if large else 36
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        fs = 20 if large else 14
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,{0.12 if large else 0.07});
                color: {styles.TEXT_PRIMARY};
                border: none;
                border-radius: {size//2}px;
                font-size: {fs}px;
                font-family: {styles.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,{0.20 if large else 0.12});
            }}
            QPushButton:pressed {{
                background: rgba(255,255,255,0.05);
            }}
        """)


def _trunc(s: str, n: int) -> str:
    return s[:n-1] + "…" if len(s) > n else s
