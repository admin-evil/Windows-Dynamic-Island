"""
Activity manager.

Maintains the ordered list of currently active activities,
emitting signals whenever the active set changes.

Priority rule: lowest priority number wins (0 = most urgent).
"""
from PyQt5.QtCore import QObject, pyqtSignal
from activities.base import Activity


class ActivityManager(QObject):
    # Emitted whenever the active activity list changes
    active_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activities: list[Activity] = []

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, activity: Activity):
        """Add an activity to the manager and connect its signals."""
        if activity not in self._activities:
            self._activities.append(activity)
            activity.started.connect(self.active_changed)
            activity.stopped.connect(self.active_changed)
            activity.changed.connect(self.active_changed)

    def unregister(self, activity: Activity):
        if activity in self._activities:
            self._activities.remove(activity)

    # ── Query ─────────────────────────────────────────────────────────────────

    def active(self) -> list[Activity]:
        """Returns currently active activities sorted by priority (lowest first)."""
        return sorted(
            [a for a in self._activities if a.is_active],
            key=lambda a: a.priority
        )

    def primary(self) -> Activity | None:
        """The highest-priority active activity, or None."""
        active = self.active()
        return active[0] if active else None

    def secondary(self) -> Activity | None:
        """Second-highest-priority active activity (for split view)."""
        active = self.active()
        return active[1] if len(active) >= 2 else None

    def count(self) -> int:
        return len(self.active())

    def has_activity(self, name: str) -> bool:
        return any(a.name == name and a.is_active for a in self._activities)

    def get(self, name: str) -> Activity | None:
        for a in self._activities:
            if a.name == name:
                return a
        return None

    def stop_all(self):
        for a in self._activities:
            try:
                a.stop()
            except Exception:
                pass
