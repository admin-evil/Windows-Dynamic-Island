"""
Clipboard activity – monitors the system clipboard.

Maintains a history of the last 10 copied text items.
History is shown in the expanded panel with one-click copy-back.
Persisted across restarts in ~/.dynamic_island/clipboard.json
"""
import json
from pathlib import Path
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QFont

import styles
from activities.base import Activity

CLIP_FILE = Path.home() / ".dynamic_island" / "clipboard.json"
MAX_ITEMS  = 10


class ClipboardActivity(Activity):
    priority = 6
    name     = "clipboard"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: list[dict] = []
        self._last_text: str = ""
        self._load()

        # Poll clipboard every 1.5 s
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._check)
        self._poll.start(1500)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        try:
            if CLIP_FILE.exists():
                self._history = json.loads(CLIP_FILE.read_text(encoding="utf-8"))
        except Exception:
            self._history = []

    def _save(self):
        try:
            CLIP_FILE.parent.mkdir(parents=True, exist_ok=True)
            CLIP_FILE.write_text(
                json.dumps(self._history, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    # ── Clipboard polling ─────────────────────────────────────────────────────

    def _check(self):
        try:
            app = QApplication.instance()
            if app is None:
                return
            cb   = app.clipboard()
            text = (cb.text() or "").strip()
            if not text or text == self._last_text:
                return
            # Ignore very short items (accidental copies)
            if len(text) < 2:
                return
            self._last_text = text
            # Add to front, deduplicate, cap at MAX_ITEMS
            self._history = [
                h for h in self._history
                if h.get("text") != text
            ]
            self._history.insert(0, {
                "text": text,
                "ts":   datetime.now().strftime("%H:%M"),
                "id":   int(datetime.now().timestamp() * 1000),
            })
            self._history = self._history[:MAX_ITEMS]
            self._save()
            self.changed.emit()
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────────────────

    def clear_history(self):
        self._history = []
        self._save()
        self._set_active(False)
        self.changed.emit()

    def copy_item(self, item_id: int):
        """Put a history item back on the clipboard."""
        for h in self._history:
            if h.get("id") == item_id:
                try:
                    QApplication.instance().clipboard().setText(h["text"])
                    self._last_text = h["text"]
                except Exception:
                    pass
                break

    # ── Activity interface ────────────────────────────────────────────────────

    @property
    def live_data(self) -> dict:
        n    = len(self._history)
        last = self._history[0]["text"] if self._history else ""
        trunc = last[:20] + "…" if len(last) > 20 else last
        return {
            "icon":  "📋",
            "label": trunc or "Zwischenablage",
            "sub":   f"{n} Einträge",
            "color": styles.ACCENT_CYAN,
        }

    def create_expanded_widget(self):
        return _ClipboardWidget(self)

    def stop(self):
        self._poll.stop()


# ── Expanded widget ───────────────────────────────────────────────────────────

class _ClipboardWidget(QWidget):
    def __init__(self, activity: ClipboardActivity, parent=None):
        super().__init__(parent)
        self._act = activity
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()
        activity.changed.connect(self._refresh)
        self._refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Verlauf")
        tf = QFont(styles.FONT_FAMILY, 11)
        tf.setWeight(QFont.Medium)
        tf.setLetterSpacing(QFont.PercentageSpacing, 115)
        title.setFont(tf)
        title.setStyleSheet(f"color: {styles.TEXT_TERTIARY}; background: transparent;")

        clear_btn = QPushButton("Löschen")
        clear_btn.setFixedHeight(22)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {styles.ACCENT_RED};
                border: none;
                font-size: 11px;
                font-family: {styles.FONT_FAMILY};
            }}
            QPushButton:hover {{ color: #FF6B6B; }}
        """)
        clear_btn.clicked.connect(self._act.clear_history)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(clear_btn)
        root.addLayout(hdr)

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(200)

        self._container = QWidget()
        self._container.setAttribute(Qt.WA_TranslucentBackground)
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addStretch()

        scroll.setWidget(self._container)
        root.addWidget(scroll)

    def _refresh(self):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in self._act._history:
            card = _ClipCard(item, self._act)
            self._layout.insertWidget(self._layout.count() - 1, card)


class _ClipCard(QWidget):
    def __init__(self, item: dict, activity: ClipboardActivity, parent=None):
        super().__init__(parent)
        self._item = item
        self._act  = activity
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 9px;
        """)
        self.setCursor(Qt.PointingHandCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 7, 8, 7)
        row.setSpacing(8)

        # Text preview
        text = item["text"]
        # Collapse whitespace for display
        preview = " ".join(text.split())
        trunc   = preview[:40] + "…" if len(preview) > 40 else preview

        lbl = QLabel(trunc)
        lf  = QFont(styles.FONT_FAMILY, 11)
        lbl.setFont(lf)
        lbl.setStyleSheet(f"color: {styles.TEXT_PRIMARY}; background: transparent;")

        ts = QLabel(item.get("ts", ""))
        tf = QFont(styles.FONT_FAMILY, 10)
        ts.setFont(tf)
        ts.setStyleSheet(f"color: {styles.TEXT_TERTIARY}; background: transparent;")
        ts.setFixedWidth(36)
        ts.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row.addWidget(lbl, 1)
        row.addWidget(ts)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._act.copy_item(self._item["id"])
        super().mousePressEvent(e)
