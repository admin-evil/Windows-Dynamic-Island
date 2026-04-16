"""
Windows DWM / Acrylic blur helper.

Applies the system-level frosted-glass blur behind the island window.
Works on Windows 10 (1903+) and Windows 11.
Falls back silently on older systems or non-Windows platforms.
"""
import ctypes
import ctypes.wintypes as wintypes
import sys


# ── Win32 structures ──────────────────────────────────────────────────────────

class _ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",   ctypes.c_uint),
        ("AccentFlags",   ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),   # AABBGGRR
        ("AnimationId",   ctypes.c_uint),
    ]


class _WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute",   ctypes.c_int),
        ("Data",        ctypes.POINTER(ctypes.c_int)),
        ("SizeOfData",  ctypes.c_size_t),
    ]


# AccentState values
_ACCENT_DISABLED              = 0
_ACCENT_ENABLE_BLURBEHIND     = 3
_ACCENT_ENABLE_ACRYLICBLUR    = 4   # Win10 1903+ / Win11

_WCA_ACCENT_POLICY = 19


# ── Public API ────────────────────────────────────────────────────────────────

def apply_blur(hwnd: int, opacity: int = 200) -> bool:
    """
    Apply acrylic / blur-behind to a window by its HWND.

    opacity : 0–255, controls the tint alpha (lower = more transparent)
    Returns True if successfully applied.
    """
    if sys.platform != "win32":
        return False
    try:
        # AABBGGRR format – black tint with given opacity
        gradient_color = (opacity << 24) | 0x000000

        accent = _ACCENT_POLICY()
        accent.AccentState   = _ACCENT_ENABLE_ACRYLICBLUR
        accent.AccentFlags   = 2
        accent.GradientColor = gradient_color

        data = _WINCOMPATTRDATA()
        data.Attribute   = _WCA_ACCENT_POLICY
        data.SizeOfData  = ctypes.sizeof(accent)
        data.Data        = ctypes.cast(
            ctypes.pointer(accent), ctypes.POINTER(ctypes.c_int)
        )

        ctypes.windll.user32.SetWindowCompositionAttribute(
            ctypes.c_int(hwnd), ctypes.byref(data)
        )
        return True
    except Exception:
        return False


def remove_blur(hwnd: int):
    """Remove acrylic effect."""
    if sys.platform != "win32":
        return
    try:
        accent = _ACCENT_POLICY()
        accent.AccentState = _ACCENT_DISABLED

        data = _WINCOMPATTRDATA()
        data.Attribute  = _WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data       = ctypes.cast(
            ctypes.pointer(accent), ctypes.POINTER(ctypes.c_int)
        )
        ctypes.windll.user32.SetWindowCompositionAttribute(
            ctypes.c_int(hwnd), ctypes.byref(data)
        )
    except Exception:
        pass
