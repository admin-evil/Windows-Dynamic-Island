"""
Auto-update checker for Dynamic Island.
Checks GitHub releases and notifies user of available updates.
"""
import json
from threading import Thread
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from version import __version__

try:
    from packaging import version as pkg_version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class UpdateChecker(QObject):
    """Checks for updates from GitHub releases."""

    update_available = pyqtSignal(str, str)  # (new_version, download_url)
    check_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.repo_url = "https://api.github.com/repos/admin-evil/Windows-Dynamic-Island"
        self.current_version = __version__

    def check_for_updates(self):
        """Check GitHub for the latest release (non-blocking)."""
        thread = QThread()
        thread.run = self._check_updates
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _check_updates(self):
        """Fetch and compare versions."""
        if not HAS_REQUESTS or not HAS_PACKAGING:
            # Skip update check if dependencies not available
            return

        try:
            response = requests.get(
                f"{self.repo_url}/releases/latest",
                timeout=5,
                headers={"Accept": "application/vnd.github.v3+json"}
            )

            if response.status_code == 200:
                release = response.json()
                latest_version = release.get("tag_name", "").lstrip("v")

                # Only proceed if we can parse both versions
                if latest_version:
                    try:
                        current = pkg_version.parse(self.current_version)
                        latest = pkg_version.parse(latest_version)

                        if latest > current:
                            # Find download URL (.exe)
                            download_url = None
                            for asset in release.get("assets", []):
                                if asset["name"].endswith(".exe"):
                                    download_url = asset["browser_download_url"]
                                    break

                            if download_url:
                                self.update_available.emit(latest_version, download_url)
                    except Exception:
                        # Invalid version format, skip
                        pass

        except Exception as e:
            # Silent fail - don't bother user with network errors
            pass
        finally:
            self.check_complete.emit()


def show_update_dialog(parent, new_version, download_url):
    """Show update notification dialog."""
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5.QtGui import QDesktopServices
    from PyQt5.QtCore import QUrl

    reply = QMessageBox.information(
        parent,
        "Update Available",
        f"Dynamic Island v{new_version} is now available.\n\nYou are currently running v{__version__}.\n\nWould you like to download it?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes
    )

    if reply == QMessageBox.Yes:
        QDesktopServices.openUrl(QUrl(download_url))
