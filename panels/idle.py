"""
Idle panel – shown when no activity is active.
Very minimal: current time + optional privacy indicator dots.
"""
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore    import Qt, QTimer
from PyQt5.QtGui     import QFont, QColor, QPainter
import styles


class IdlePanel(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000)
        self._tick()

    def _build(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(18, 0, 18, 0)
        row.setSpacing(6)

        s = self.config.get_font_scale()

        self.time_lbl = QLabel("--:--")
        tf = QFont(styles.FONT_FAMILY, int(14 * s))
        tf.setWeight(QFont.Light)
        tf.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        self.time_lbl.setFont(tf)
        self.time_lbl.setStyleSheet(
            f"color: {styles.TEXT_PRIMARY}; background: transparent;"
        )

        # Privacy dots container (right)
        self.dot_row = QHBoxLayout()
        self.dot_row.setSpacing(4)
        self.dot_row.setContentsMargins(0, 0, 0, 0)

        row.addWidget(self.time_lbl)
        row.addStretch()
        row.addLayout(self.dot_row)

    def _tick(self):
        self.time_lbl.setText(datetime.now().strftime("%H:%M"))

    def show_privacy_dot(self, color: str, visible: bool):
        """Show or hide a colored privacy indicator dot."""
        # Clear existing dots and rebuild
        while self.dot_row.count():
            item = self.dot_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if visible:
            dot = _PrivacyDot(color)
            self.dot_row.addWidget(dot)


class _PrivacyDot(QWidget):
    SIZE = 8

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self._color = QColor(color)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, self.SIZE, self.SIZE)
