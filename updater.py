"""
Auto-update checker for Dynamic Island.
Checks GitHub releases and notifies user of available updates.
"""
import json
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer

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


class UpdateWorker(QObject):
    """Worker for checking updates in a separate thread."""

    update_available = pyqtSignal(str, str)  # (new_version, download_url)
    finished = pyqtSignal()

    def __init__(self, repo_url, current_version):
        super().__init__()
        self.repo_url = repo_url
        self.current_version = current_version

    def check(self):
        """Check for updates."""
        if not HAS_REQUESTS or not HAS_PACKAGING:
            self.finished.emit()
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

                if latest_version:
                    try:
                        current = pkg_version.parse(self.current_version)
                        latest = pkg_version.parse(latest_version)

                        if latest > current:
                            download_url = None
                            for asset in release.get("assets", []):
                                if asset["name"].endswith(".exe"):
                                    download_url = asset["browser_download_url"]
                                    break

                            if download_url:
                                self.update_available.emit(latest_version, download_url)
                    except Exception:
                        pass

        except Exception:
            pass
        finally:
            self.finished.emit()


class UpdateChecker(QObject):
    """Checks for updates from GitHub releases."""

    update_available = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.repo_url = "https://api.github.com/repos/admin-evil/Windows-Dynamic-Island"
        self.current_version = __version__
        self.thread = None
        self.worker = None

    def check_for_updates(self):
        """Check GitHub for the latest release (non-blocking)."""
        # Use QTimer instead of threading to avoid Qt issues
        QTimer.singleShot(100, self._do_check)

    def _do_check(self):
        """Perform the actual check."""
        if not HAS_REQUESTS or not HAS_PACKAGING:
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

                if latest_version:
                    try:
                        current = pkg_version.parse(self.current_version)
                        latest = pkg_version.parse(latest_version)

                        if latest > current:
                            download_url = None
                            for asset in release.get("assets", []):
                                if asset["name"].endswith(".exe"):
                                    download_url = asset["browser_download_url"]
                                    break

                            if download_url:
                                self.update_available.emit(latest_version, download_url)
                    except Exception:
                        pass

        except Exception:
            pass


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
