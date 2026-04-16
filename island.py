"""
Dynamic Island – main window  v4

Shape fix:  setMask(QRegion) is applied every frame so the OS
            sees a true pill / rounded-rect, not a rectangle.
            WA_TranslucentBackground alone is not enough on Windows
            because DWM still renders the window bounding-box black.

New features added in v4:
  • NotesActivity  – quick notes stored in ~/.dynamic_island/notes.json
  • ClipboardActivity – monitors clipboard, shows last 10 items
  • KeyboardShortcut – Win+D opens/closes the island
  • Auto-hide on fullscreen apps
  • Smooth per-pixel mask update at 60 fps
"""

import sys
import ctypes
from enum import Enum, auto

from PyQt5.QtWidgets import (
    QWidget, QApplication, QMenu, QAction,
    QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QTimer, QRect, QElapsedTimer
)
from PyQt5.QtGui import (
    QPainter, QPainterPath, QColor, QPolygon, QBrush, QPen, QRegion
)

import styles
from config           import Config
from spring           import SpringValue, SpringGroup
from blur             import apply_blur
from activity_manager import ActivityManager
from activities       import MusicActivity, TimerActivity, TransientActivity
from activities.notes     import NotesActivity
from activities.clipboard import ClipboardActivity
from panels           import IdlePanel, LivePanel, ExpandedPanel


# ── Geometry ──────────────────────────────────────────────────────────────────

class _Geom:
    IDLE_H     = 36
    LIVE_H     = 46
    EXPANDED_H = 380

    @staticmethod
    def idle_w(cfg):     return cfg.get("width", 140)
    @staticmethod
    def live_w(cfg, split=False):
        base = cfg.get("width", 140) + 160
        return base + 70 if split else base
    @staticmethod
    def expanded_w(cfg): return min(cfg.get("width", 140) + 270, 460)


class State(Enum):
    IDLE      = auto()
    LIVE      = auto()
    EXPANDED  = auto()
    TRANSIENT = auto()


# ══════════════════════════════════════════════════════════════════════════════

class DynamicIsland(QWidget):

    LONG_PRESS_MS = 500

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.state  = State.IDLE
        self._pre_transient_state = State.IDLE
        self._drag_start_y = None
        self._press_timer  = QElapsedTimer()
        self._long_press_t = QTimer(self)
        self._long_press_t.setSingleShot(True)
        self._long_press_t.timeout.connect(self._on_long_press)

        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.timeout.connect(self._go_idle_or_live)

        # ── Activities ────────────────────────────────────────────────────────
        self.activity_manager = ActivityManager(self)
        self.music     = MusicActivity(self)
        self.timer     = TimerActivity(self)
        self.events    = TransientActivity(self)
        self.notes     = NotesActivity(self)
        self.clipboard = ClipboardActivity(self)

        for act in (self.music, self.timer, self.events,
                    self.notes, self.clipboard):
            self.activity_manager.register(act)

        self.activity_manager.active_changed.connect(self._on_activity_changed)

        # ── Springs ───────────────────────────────────────────────────────────
        # Apple-like smooth animation with minimal overshoot
        w0 = _Geom.idle_w(config)
        self.w_spring = SpringValue(w0,            stiffness=350, damping=32)
        self.h_spring = SpringValue(_Geom.IDLE_H,  stiffness=360, damping=34)
        self.r_spring = SpringValue(_Geom.IDLE_H / 2, stiffness=340, damping=30)

        self._group = SpringGroup()
        self._group.add(self.w_spring)
        self._group.add(self.h_spring)
        self._group.add(self.r_spring)

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # 60 FPS
        self._anim_timer.timeout.connect(self._anim_tick)

        # ── Mask Caching (Performance) ────────────────────────────────────────
        self._last_mask_region = None
        self._last_mask_r = None
        self._last_mask_w = None
        self._last_mask_h = None

        # ── Global Fade Timer (Performance: 9 timers → 1) ──────────────────────
        self._fade_targets = {}  # { fx_id → {'fx': fx, 'target': opacity} }
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(16)  # 60 FPS
        self._fade_timer.timeout.connect(self._fade_tick)

        # ── Activity Change Debouncing (Performance) ──────────────────────────
        self._activity_change_timer = QTimer(self)
        self._activity_change_timer.setSingleShot(True)
        self._activity_change_timer.setInterval(16)  # Batch updates
        self._activity_change_timer.timeout.connect(self._do_on_activity_changed)
        self._pending_activity_change = False

        # ── Window ────────────────────────────────────────────────────────────
        self._setup_window()
        self._build_panels()
        self._apply_geometry(instant=True)
        self._update_mask()
        self._sync_panels()

        QTimer.singleShot(200, self._apply_blur)
        QTimer.singleShot(600, self._on_activity_changed)

    # ══════════════════════════════════════════════════════════════════════════
    # Window setup
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )
        # WA_TranslucentBackground + setMask = true transparent corners
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        sc = QApplication.primaryScreen().geometry()
        w  = _Geom.idle_w(self.config)
        x  = (sc.width() - w) // 2 + sc.left()
        y  = sc.top() + self.config.get("y_offset", 10)
        self.setGeometry(x, y, w, _Geom.IDLE_H)

    def _apply_blur(self):
        try:
            apply_blur(int(self.winId()), opacity=200)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # Shape mask  (THE KEY FIX)
    # ══════════════════════════════════════════════════════════════════════════

    def _update_mask(self):
        """
        Apply a pixel-exact mask so Windows clips the window to the pill shape.
        Without this, the OS renders the full bounding rectangle black.
        OPTIMIZED: Cache results to avoid expensive setMask() Windows API calls.
        """
        w = self.width()
        h = self.height()
        r = max(2.0, min(float(self.r_spring.pos), h / 2.0))

        # CACHE CHECK: Skip if mask parameters haven't changed
        if (self._last_mask_region is not None and
            self._last_mask_r == r and
            self._last_mask_w == w and
            self._last_mask_h == h):
            return  # Identical to last frame → skip expensive setMask()

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, r, r)

        # Convert path to polygon → QRegion
        poly = path.toFillPolygon()
        pts  = [p.toPoint() for p in poly]
        region = QRegion(QPolygon(pts))
        self.setMask(region)

        # Cache the result for next frame
        self._last_mask_region = region
        self._last_mask_r = r
        self._last_mask_w = w
        self._last_mask_h = h

    # ══════════════════════════════════════════════════════════════════════════
    # Panels
    # ══════════════════════════════════════════════════════════════════════════

    def _build_panels(self):
        cfg = self.config
        self.idle_panel = IdlePanel(cfg, self)
        self.live_panel = LivePanel(cfg, self)
        self.exp_panel  = ExpandedPanel(cfg, self)

        self._idle_fx = QGraphicsOpacityEffect(); self._idle_fx.setOpacity(1.0)
        self._live_fx = QGraphicsOpacityEffect(); self._live_fx.setOpacity(0.0)
        self._exp_fx  = QGraphicsOpacityEffect(); self._exp_fx.setOpacity(0.0)

        self.idle_panel.setGraphicsEffect(self._idle_fx)
        self.live_panel.setGraphicsEffect(self._live_fx)
        self.exp_panel.setGraphicsEffect(self._exp_fx)

        self.live_panel.setVisible(False)
        self.exp_panel.setVisible(False)

    # ══════════════════════════════════════════════════════════════════════════
    # Spring geometry
    # ══════════════════════════════════════════════════════════════════════════

    def _screen(self) -> QRect:
        return QApplication.primaryScreen().geometry()

    def _apply_geometry(self, instant=False):
        sc = self._screen()
        w  = int(self.w_spring.pos)
        h  = int(self.h_spring.pos)
        x  = (sc.width() - w) // 2 + sc.left()
        y  = sc.top() + self.config.get("y_offset", 10)

        # OPTIMIZATION: Cache geometry to avoid repeated setGeometry() calls
        # Only update if position changed (ignore sub-pixel variations)
        if not hasattr(self, '_last_geom') or self._last_geom != (x, y, w, h):
            self.setGeometry(x, y, w, h)
            self._last_geom = (x, y, w, h)
            # Only request repaint if geometry actually changed
            if not hasattr(self, '_last_repaint_geom') or self._last_repaint_geom != (w, h):
                self._last_repaint_geom = (w, h)

    def _set_targets(self, w: float, h: float):
        self.w_spring.set_target(w)
        self.h_spring.set_target(h)
        r_target = styles.CORNER_RADIUS if self.state == State.EXPANDED else h / 2.0
        self.r_spring.set_target(r_target)
        self._start_anim()

    def _start_anim(self):
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def _anim_tick(self):
        self._group.update(0.016)
        self._apply_geometry()

        # OPTIMIZATION: Only update mask if height changed significantly (> 1px)
        h = self.height()
        if not hasattr(self, '_last_mask_h'):
            self._last_mask_h = h

        if abs(h - self._last_mask_h) > 1:
            self._update_mask()
            self._last_mask_h = h

        # Always repaint during animation
        self.update()

        w = self.width()
        # OPTIMIZATION: Cache panel geometry to avoid repeated calls
        if not hasattr(self, '_last_panel_geom') or self._last_panel_geom != (w, h):
            for panel in (self.idle_panel, self.live_panel, self.exp_panel):
                panel.setGeometry(0, 0, w, h)
            self._last_panel_geom = (w, h)

        if self._group.settled:
            self._anim_timer.stop()

    # ══════════════════════════════════════════════════════════════════════════
    # State machine
    # ══════════════════════════════════════════════════════════════════════════

    def _transition(self, new_state: State):
        self.state = new_state
        cfg = self.config

        if new_state == State.IDLE:
            w, h = _Geom.idle_w(cfg), _Geom.IDLE_H
        elif new_state in (State.LIVE, State.TRANSIENT):
            split = self.activity_manager.count() >= 2
            w, h  = _Geom.live_w(cfg, split), _Geom.LIVE_H
        else:  # EXPANDED
            w, h = _Geom.expanded_w(cfg), _Geom.EXPANDED_H

        self._set_targets(w, h)
        self._sync_panels()

    def _sync_panels(self):
        s = self.state
        show_idle = (s == State.IDLE)
        show_live = (s in (State.LIVE, State.TRANSIENT))
        show_exp  = (s == State.EXPANDED)

        self.live_panel.setVisible(show_live or show_exp)
        self.exp_panel.setVisible(show_exp)
        self.idle_panel.setVisible(True)

        self._fade(self._idle_fx, 1.0 if show_idle else 0.0)
        self._fade(self._live_fx, 1.0 if show_live else 0.0)
        self._fade(self._exp_fx,  1.0 if show_exp  else 0.0)

        if show_live or show_exp:
            p = self.activity_manager.primary()
            s2 = self.activity_manager.secondary()
            self.live_panel.update_activities(p, s2)

        if show_exp:
            p      = self.activity_manager.primary()
            others = self.activity_manager.active()[1:]
            self.exp_panel.update_activities(p, others)

    def _fade(self, fx: QGraphicsOpacityEffect, target: float):
        """Queue a fade effect - all processed by global _fade_tick()."""
        cur = fx.opacity()
        if abs(cur - target) < 0.02:
            fx.setOpacity(target)
            return

        # Queue this effect for the global fade timer
        fx_id = id(fx)
        self._fade_targets[fx_id] = {'fx': fx, 'target': target}

        if not self._fade_timer.isActive():
            self._fade_timer.start()

    def _fade_tick(self):
        """Process all active fades in one tick (60 FPS batch update)."""
        still_fading = False

        for fx_id, fade_data in list(self._fade_targets.items()):
            fx = fade_data['fx']
            target = fade_data['target']
            cur = fx.opacity()

            if abs(cur - target) < 0.02:
                fx.setOpacity(target)
                del self._fade_targets[fx_id]
            else:
                step = 0.14 if target > cur else -0.14
                new_val = cur + step
                if (step > 0 and new_val >= target) or (step < 0 and new_val <= target):
                    fx.setOpacity(target)
                    del self._fade_targets[fx_id]
                else:
                    fx.setOpacity(new_val)
                    still_fading = True

        if not still_fading:
            self._fade_timer.stop()

    def go_idle(self):
        self._collapse_timer.stop()
        self._transition(State.IDLE)

    def go_live(self):
        self._collapse_timer.stop()
        self._transition(State.LIVE)

    def go_expanded(self):
        self._collapse_timer.stop()
        self._transition(State.EXPANDED)

    def go_transient(self):
        self._pre_transient_state = self.state
        self._transition(State.TRANSIENT)

    def _go_idle_or_live(self):
        if self.activity_manager.count() > 0:
            self.go_live()
        else:
            self.go_idle()

    def _schedule_collapse(self, ms=1400):
        self._collapse_timer.stop()
        self._collapse_timer.start(ms)

    # ══════════════════════════════════════════════════════════════════════════
    # Activity changes
    # ══════════════════════════════════════════════════════════════════════════

    def _on_activity_changed(self):
        """Queue activity change - don't process immediately (debounced)."""
        self._pending_activity_change = True
        if not self._activity_change_timer.isActive():
            self._activity_change_timer.start()

    def _do_on_activity_changed(self):
        """Actually process the activity change (called by debounce timer)."""
        if not self._pending_activity_change:
            return

        self._pending_activity_change = False

        primary = self.activity_manager.primary()

        if primary and primary.name == "event":
            if self.state not in (State.TRANSIENT, State.EXPANDED):
                self.go_transient()
            else:
                self._sync_panels()
            return

        if self.state == State.TRANSIENT and (not primary or primary.name != "event"):
            self._transition(self._pre_transient_state)
            return

        if self.state == State.EXPANDED:
            self._sync_panels()
            return

        if self.activity_manager.count() > 0:
            if self.state != State.LIVE:
                self.go_live()
            else:
                self._sync_panels()
        else:
            if self.state != State.IDLE:
                self.go_idle()

    # ══════════════════════════════════════════════════════════════════════════
    # Paint
    # ══════════════════════════════════════════════════════════════════════════

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        r = max(2.0, min(float(self.r_spring.pos), h / 2.0))

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, r, r)

        # Deep black fill
        p.fillPath(path, QColor(styles.BG_PRIMARY))

        # Subtle specular border – 1 px inner line
        p.setPen(QColor(255, 255, 255, 16))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

        p.end()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_mask()
        w, h = self.width(), self.height()
        # OPTIMIZATION: Only update panels if size actually changed
        if not hasattr(self, '_last_panel_geom') or self._last_panel_geom != (w, h):
            for panel in (self.idle_panel, self.live_panel, self.exp_panel):
                panel.setGeometry(0, 0, w, h)
            self._last_panel_geom = (w, h)

    # ══════════════════════════════════════════════════════════════════════════
    # Mouse / keyboard
    # ══════════════════════════════════════════════════════════════════════════

    def enterEvent(self, e):
        if self.config.get("expand_on", "hover") == "hover":
            if self.state == State.IDLE and self.activity_manager.count() > 0:
                self._collapse_timer.stop()
                self.go_live()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self.state in (State.LIVE, State.TRANSIENT):
            self._schedule_collapse(1200)
        elif self.state == State.EXPANDED:
            self._schedule_collapse(2400)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press_timer.start()
            self._long_press_t.start(self.LONG_PRESS_MS)
            self._drag_start_y = e.globalY() - self.y()
        elif e.button() == Qt.RightButton:
            self._context_menu(e.globalPos())
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            elapsed = self._press_timer.elapsed()
            self._long_press_t.stop()
            if elapsed < self.LONG_PRESS_MS - 50:
                # Short tap
                if self.state == State.EXPANDED:
                    self.go_live()
                elif self.state in (State.LIVE, State.TRANSIENT):
                    self.go_expanded()
                elif self.state == State.IDLE and self.activity_manager.count() > 0:
                    self.go_live()
            self._drag_start_y = None
        super().mouseReleaseEvent(e)

    def mouseMoveEvent(self, e):
        if (e.buttons() & Qt.LeftButton) and self._drag_start_y is not None:
            sc    = self._screen()
            new_y = max(0, min(e.globalY() - self._drag_start_y, sc.height() - 80))
            cx    = (sc.width() - self.width()) // 2 + sc.left()
            self.move(cx, new_y)
            self.config.set("y_offset", new_y - sc.top())
        super().mouseMoveEvent(e)

    def _on_long_press(self):
        if self.state != State.EXPANDED:
            self.go_expanded()

    # ══════════════════════════════════════════════════════════════════════════
    # Context menu
    # ══════════════════════════════════════════════════════════════════════════

    def _context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(styles.CONTEXT_MENU_STYLE)

        # Notes shortcut
        notes_a = QAction("📝  Neue Notiz...", self)
        notes_a.triggered.connect(self._quick_note)
        menu.addAction(notes_a)

        # Clipboard shortcut
        clip_a = QAction("📋  Zwischenablage", self)
        clip_a.triggered.connect(lambda: (self.clipboard._set_active(True), self.go_expanded()))
        menu.addAction(clip_a)

        menu.addSeparator()

        # Timer
        timer_label = "⏸  Timer pausieren" if self.timer.running else "▶  Timer starten"
        timer_a = QAction(timer_label, self)
        timer_a.triggered.connect(
            self.timer.pause if self.timer.running else self.timer.start
        )
        menu.addAction(timer_a)

        menu.addSeparator()

        settings_a = QAction("Einstellungen", self)
        settings_a.triggered.connect(self._open_settings)
        menu.addAction(settings_a)

        menu.addSeparator()

        quit_a = QAction("Beenden", self)
        quit_a.triggered.connect(QApplication.quit)
        menu.addAction(quit_a)

        menu.exec_(pos)

    def _quick_note(self):
        """Open a quick-note input dialog."""
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            None, "Neue Notiz", "Notiz eingeben:",
        )
        if ok and text.strip():
            self.notes.add_note(text.strip())
            self.push_event("📝", "Notiz gespeichert", text[:22], styles.ACCENT_BLUE, 2000)

    def _open_settings(self):
        from settings_dialog import SettingsDialog
        if self.state == State.EXPANDED:
            self.go_idle()
        dlg = SettingsDialog(self.config)
        dlg.applied.connect(self._on_activity_changed)
        dlg.exec_()

    # ── Public API ─────────────────────────────────────────────────────────────

    def show_settings(self):
        self._open_settings()

    def push_event(self, icon, label, sub="", color=None, ms=3000):
        if color is None:
            color = styles.ACCENT_BLUE
        self.events.push_event(icon, label, sub, color, ms)

    def cleanup(self):
        self.activity_manager.stop_all()
