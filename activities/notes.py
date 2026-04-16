"""
Notes activity – persistent quick notes.

Notes are stored in ~/.dynamic_island/notes.json
The expanded view shows a clean list with add/delete controls.
The compact live pill shows the note count.
"""
import json
from pathlib import Path
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QLineEdit,
    QSizePolicy, QApplication
)
from PyQt5.QtCore    import Qt, QTimer
from PyQt5.QtGui     import QFont, QColor

import styles
from activities.base import Activity

NOTES_FILE = Path.home() / ".dynamic_island" / "notes.json"


class NotesActivity(Activity):
    priority = 5
    name     = "notes"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notes: list[dict] = []
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        try:
            if NOTES_FILE.exists():
                self._notes = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        except Exception:
            self._notes = []

    def _save(self):
        try:
            NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
            NOTES_FILE.write_text(
                json.dumps(self._notes, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    # ── API ───────────────────────────────────────────────────────────────────

    def add_note(self, text: str):
        self._notes.insert(0, {
            "text": text,
            "ts": datetime.now().strftime("%d.%m.  %H:%M"),
            "id": int(datetime.now().timestamp() * 1000),
        })
        self._save()
        self._set_active(True)
        self.changed.emit()

    def delete_note(self, note_id: int):
        self._notes = [n for n in self._notes if n.get("id") != note_id]
        self._save()
        if not self._notes:
            self._set_active(False)
        self.changed.emit()

    @property
    def notes(self) -> list[dict]:
        return list(self._notes)

    # ── Activity interface ────────────────────────────────────────────────────

    @property
    def live_data(self) -> dict:
        n = len(self._notes)
        last = self._notes[0]["text"] if self._notes else ""
        trunc = last[:20] + "…" if len(last) > 20 else last
        return {
            "icon":  "📝",
            "label": trunc or "Notizen",
            "sub":   f"{n} Notiz" + ("en" if n != 1 else ""),
            "color": styles.ACCENT_BLUE,
        }

    def create_expanded_widget(self):
        return _NotesWidget(self)


# ── Expanded widget ───────────────────────────────────────────────────────────

class _NotesWidget(QWidget):
    def __init__(self, activity: NotesActivity, parent=None):
        super().__init__(parent)
        self._act = activity
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()
        activity.changed.connect(self._refresh)
        self._refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Neue Notiz…")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255,255,255,0.07);
                color: {styles.TEXT_PRIMARY};
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 10px;
                padding: 7px 12px;
                font-family: {styles.FONT_FAMILY};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {styles.ACCENT_BLUE};
            }}
        """)
        self.input.returnPressed.connect(self._add)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {styles.ACCENT_BLUE};
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 18px;
                font-family: {styles.FONT_FAMILY};
                font-weight: 300;
            }}
            QPushButton:hover {{ background: #0070E0; }}
        """)
        add_btn.clicked.connect(self._add)

        input_row.addWidget(self.input, 1)
        input_row.addWidget(add_btn)
        root.addLayout(input_row)

        # Notes list (scrollable)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background: transparent;")
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(200)

        self._list_container = QWidget()
        self._list_container.setAttribute(Qt.WA_TranslucentBackground)
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_container)
        root.addWidget(self._scroll)

    def _add(self):
        text = self.input.text().strip()
        if text:
            self._act.add_note(text)
            self.input.clear()

    def _refresh(self):
        # Clear existing note cards
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for note in self._act.notes:
            card = _NoteCard(note, self._act)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)


class _NoteCard(QWidget):
    def __init__(self, note: dict, activity: NotesActivity, parent=None):
        super().__init__(parent)
        self._note = note
        self._act  = activity
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 8, 8)
        row.setSpacing(8)

        # Text column
        col = QVBoxLayout()
        col.setSpacing(2)

        txt = QLabel(note["text"])
        txt_f = QFont(styles.FONT_FAMILY, 12)
        txt_f.setWeight(QFont.Normal)
        txt.setFont(txt_f)
        txt.setStyleSheet(f"color: {styles.TEXT_PRIMARY}; background: transparent;")
        txt.setWordWrap(True)

        ts = QLabel(note.get("ts", ""))
        ts_f = QFont(styles.FONT_FAMILY, 10)
        ts.setFont(ts_f)
        ts.setStyleSheet(f"color: {styles.TEXT_TERTIARY}; background: transparent;")

        col.addWidget(txt)
        col.addWidget(ts)

        # Copy button
        copy_btn = _IconBtn("⎘", styles.ACCENT_BLUE)
        copy_btn.setToolTip("Kopieren")
        copy_btn.clicked.connect(self._copy)

        # Delete button
        del_btn = _IconBtn("×", styles.ACCENT_RED)
        del_btn.setToolTip("Löschen")
        del_btn.clicked.connect(self._delete)

        row.addLayout(col, 1)
        row.addWidget(copy_btn)
        row.addWidget(del_btn)

    def _copy(self):
        QApplication.clipboard().setText(self._note["text"])

    def _delete(self):
        self._act.delete_note(self._note["id"])


class _IconBtn(QPushButton):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                border: none;
                border-radius: 13px;
                font-size: 14px;
                font-family: {styles.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.08);
            }}
        """)
