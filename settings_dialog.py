"""Settings dialog v3."""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QComboBox, QFrame, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont
import styles
from config import Config


class SettingsDialog(QDialog):
    applied = pyqtSignal()

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Dynamic Island – Einstellungen")
        self.setModal(True)
        self.setFixedWidth(380)
        self.setStyleSheet(styles.SETTINGS_STYLE)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet(f"background: {styles.BG_SURFACE};")
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 8)
        root.setSpacing(0)

        # Title
        t = QLabel("Einstellungen")
        tf = QFont(styles.FONT_FAMILY, 18)
        tf.setWeight(QFont.Light)
        t.setFont(tf)
        root.addWidget(t)
        root.addSpacing(22)

        # ── Darstellung ───────────────────────────────────────────────────────
        root.addWidget(self._sec("Darstellung"))
        root.addSpacing(12)

        self.width_sl, wr = self._slider("Breite (Idle)", 80, 300,
                                          self.config.get("width", 140), " px")
        self.yoff_sl, yr  = self._slider("Abstand oben",  0, 120,
                                          self.config.get("y_offset", 10), " px")
        self.font_sl, fr  = self._slider("Textgröße",    70, 150,
                                          int(self.config.get_font_scale() * 100), " %")
        for w in (wr, yr, fr):
            root.addLayout(w)
            root.addSpacing(10)

        root.addSpacing(8)
        root.addWidget(self._hsep())
        root.addSpacing(16)

        # ── Interaktion ───────────────────────────────────────────────────────
        root.addWidget(self._sec("Interaktion"))
        root.addSpacing(12)

        exp_row = QHBoxLayout()
        lbl = QLabel("Erweitern bei")
        lbl.setFixedWidth(120)
        lbl.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; font-size: 13px;")
        self.exp_combo = QComboBox()
        self.exp_combo.addItems(["Hover (automatisch)", "Langer Druck"])
        self.exp_combo.setCurrentIndex(
            0 if self.config.get("expand_on", "hover") == "hover" else 1
        )
        exp_row.addWidget(lbl)
        exp_row.addStretch()
        exp_row.addWidget(self.exp_combo)
        root.addLayout(exp_row)
        root.addSpacing(20)

        root.addWidget(self._hsep())
        root.addSpacing(16)

        # ── Info ──────────────────────────────────────────────────────────────
        root.addWidget(self._sec("Info"))
        root.addSpacing(10)
        info = QLabel(
            "Dynamic Island erkennt Musik über Windows SMTC.\n"
            "Timer starten: Rechtsklick → Timer starten.\n"
            "Ereignisse: z. B. Akku-Warnung erscheint automatisch."
        )
        info_font = QFont(styles.FONT_FAMILY, 11)
        info.setFont(info_font)
        info.setStyleSheet(f"color: {styles.TEXT_TERTIARY}; background: transparent;")
        info.setWordWrap(True)
        root.addWidget(info)
        root.addSpacing(16)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Button bar
        bar = QWidget()
        bar.setStyleSheet(
            f"background: {styles.BG_SURFACE}; border-top: 1px solid {styles.SEPARATOR};"
        )
        btn_row = QHBoxLayout(bar)
        btn_row.setContentsMargins(28, 12, 28, 16)
        btn_row.setSpacing(10)

        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Übernehmen")
        ok.setObjectName("primary")
        ok.setDefault(True)
        ok.clicked.connect(self._apply)

        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        outer.addWidget(bar)

    def _apply(self):
        self.config.set("width",     self.width_sl.value())
        self.config.set("y_offset",  self.yoff_sl.value())
        self.config.set_font_scale(  self.font_sl.value() / 100.0)
        self.config.set("expand_on",
            "hover" if self.exp_combo.currentIndex() == 0 else "click")
        self.applied.emit()
        self.accept()

    def _sec(self, text):
        lbl = QLabel(text.upper())
        f = QFont(styles.FONT_FAMILY, 10)
        f.setWeight(QFont.DemiBold)
        f.setLetterSpacing(QFont.PercentageSpacing, 118)
        lbl.setFont(f)
        lbl.setStyleSheet(f"color: {styles.TEXT_TERTIARY};")
        return lbl

    def _hsep(self):
        s = QFrame()
        s.setFrameShape(QFrame.HLine)
        s.setFixedHeight(1)
        s.setStyleSheet(f"background: {styles.SEPARATOR}; border: none;")
        return s

    def _slider(self, label, lo, hi, val, suffix=""):
        row = QHBoxLayout()
        row.setSpacing(10)

        lbl = QLabel(label)
        lbl.setFixedWidth(120)
        lbl.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; font-size: 13px;")

        sl = QSlider(Qt.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)

        vl = QLabel(f"{val}{suffix}")
        vl.setFixedWidth(50)
        vl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vl.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; font-size: 11px;")
        sl.valueChanged.connect(lambda v: vl.setText(f"{v}{suffix}"))

        row.addWidget(lbl)
        row.addWidget(sl, 1)
        row.addWidget(vl)
        return sl, row
