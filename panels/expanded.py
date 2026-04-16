"""
Expanded panel – full overlay shown on long-press.
Routes to the correct expanded widget for the primary activity.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont, QColor, QPainter, QPainterPath
import styles
from activities.base import Activity


class ExpandedPanel(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._current_widget = None
        self._build()

    def _build(self):
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(20, 12, 20, 16)
        self._root.setSpacing(0)

        # Drag handle
        handle = _Handle()
        self._root.addWidget(handle, 0, Qt.AlignHCenter)
        self._root.addSpacing(10)

        # Content placeholder
        self._content_area = QVBoxLayout()
        self._content_area.setContentsMargins(0, 0, 0, 0)
        self._content_area.setSpacing(0)
        self._root.addLayout(self._content_area)

        self._root.addStretch()

        # Secondary activity chips
        self._chips_row = QHBoxLayout()
        self._chips_row.setSpacing(8)
        self._chips_row.setContentsMargins(0, 10, 0, 0)
        self._root.addLayout(self._chips_row)

    def update_activities(self, primary: Activity | None, others: list):
        # Remove old content widget
        if self._current_widget is not None:
            self._content_area.removeWidget(self._current_widget)
            self._current_widget.setParent(None)
            self._current_widget.deleteLater()
            self._current_widget = None

        if primary:
            w = primary.create_expanded_widget()
            w.setParent(self)
            self._content_area.addWidget(w)
            self._current_widget = w

        # Chips for secondary activities
        while self._chips_row.count():
            item = self._chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for act in others:
            chip = _ActivityChip(act.live_data, self.config)
            self._chips_row.addWidget(chip)
        if others:
            self._chips_row.addStretch()


class _Handle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 4)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(styles.TEXT_TERTIARY))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 32, 4, 2, 2)


class _ActivityChip(QWidget):
    def __init__(self, data: dict, config, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        s   = config.get_font_scale()
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 5, 12, 5)
        row.setSpacing(6)

        color = data.get("color", styles.TEXT_SECONDARY)
        icon  = QLabel(data.get("icon", ""))
        icon.setFont(QFont(styles.FONT_FAMILY, int(11 * s)))
        icon.setStyleSheet(f"color: {color}; background: transparent;")

        lbl = QLabel(data.get("label", "")[:16])
        lf  = QFont(styles.FONT_FAMILY, int(11 * s))
        lf.setWeight(QFont.Medium)
        lbl.setFont(lf)
        lbl.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; background: transparent;")

        row.addWidget(icon)
        row.addWidget(lbl)

        self.setStyleSheet("""
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
        """)
