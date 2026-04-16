"""
Live Activity panel – compact bar showing up to two active activities.

Single activity: icon + label + sub-label fills the pill
Split view:      two halves separated by a thin divider (when 2 activities)
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont

import styles
from activities.base import Activity


class LivePanel(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()

    def _build(self):
        self._row = QHBoxLayout(self)
        self._row.setContentsMargins(16, 0, 16, 0)
        self._row.setSpacing(0)

        self._left = _ActivitySlot(self.config, align="left")

        self._div = QFrame()
        self._div.setFixedSize(1, 18)
        self._div.setStyleSheet("background: rgba(255,255,255,0.15);")
        self._div.setVisible(False)

        self._right = _ActivitySlot(self.config, align="right")
        self._right.setVisible(False)

        self._row.addWidget(self._left, 1)
        self._row.addWidget(self._div)
        self._row.addSpacing(12)
        self._row.addWidget(self._right, 1)

    def update_activities(self, primary, secondary):
        if primary:
            self._left.set_data(primary.live_data)

        has_split = secondary is not None
        self._div.setVisible(has_split)
        self._right.setVisible(has_split)
        if has_split:
            self._right.set_data(secondary.live_data)


class _ActivitySlot(QWidget):
    def __init__(self, config, align="left", parent=None):
        super().__init__(parent)
        self.config = config
        self._align = align
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()

    def _build(self):
        s   = self.config.get_font_scale()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        if self._align == "right":
            row.addStretch()

        self.icon_lbl = QLabel("")
        icon_font = QFont(styles.FONT_FAMILY, int(14 * s))
        self.icon_lbl.setFont(icon_font)
        self.icon_lbl.setStyleSheet("background: transparent;")
        self.icon_lbl.setFixedWidth(20)
        self.icon_lbl.setAlignment(Qt.AlignCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.label_lbl = QLabel("")
        label_font = QFont(styles.FONT_FAMILY, int(12 * s))
        label_font.setWeight(QFont.Medium)
        self.label_lbl.setFont(label_font)
        self.label_lbl.setStyleSheet(f"color: {styles.TEXT_PRIMARY}; background: transparent;")

        self.sub_lbl = QLabel("")
        sub_font = QFont(styles.FONT_FAMILY, int(10 * s))
        self.sub_lbl.setFont(sub_font)
        self.sub_lbl.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; background: transparent;")

        text_col.addWidget(self.label_lbl)
        text_col.addWidget(self.sub_lbl)

        row.addWidget(self.icon_lbl)
        row.addLayout(text_col)

        if self._align == "left":
            row.addStretch()

    def set_data(self, data: dict):
        color = data.get("color", styles.TEXT_PRIMARY)
        self.icon_lbl.setText(data.get("icon", ""))

        # OPTIMIZATION: Only update StyleSheet if color changed
        if not hasattr(self, '_last_icon_color'):
            self._last_icon_color = None

        if self._last_icon_color != color:
            self.icon_lbl.setStyleSheet(f"color: {color}; background: transparent;")
            self._last_icon_color = color

        self.label_lbl.setText(_trunc(data.get("label", ""), 20))
        sub = data.get("sub", "")
        self.sub_lbl.setText(_trunc(sub, 18))
        self.sub_lbl.setVisible(bool(sub))


def _trunc(s, n):
    return s[:n-1] + "…" if len(s) > n else s
