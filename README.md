# Dynamic Island for Windows  ·  v1.0 BETA

 **WORK IN PROGRESS** — This is a v1.0 Beta release. The app is fully functional but still under active development. Some features may need refinement, and performance optimizations are ongoing.

A native-feeling Dynamic Island for Windows — built around a proper state machine, spring-physics animations, and a priority-driven activity system. Inspired 1:1 by Apple's specification.

---

## How it works

The island has four states that transition automatically based on what's happening on your system:

| State | Trigger | Appearance |
|---|---|---|
| **IDLE** | Nothing active | Tiny pill · time only |
| **LIVE** | Music / Timer running | Wider pill · activity info |
| **EXPANDED** | Long-press | Full overlay · controls |
| **TRANSIENT** | System event | Brief notification · auto-dismiss |

**Split view:** When two activities are active simultaneously (e.g. music + timer), the pill shows both side-by-side with a thin divider — exactly like iOS.

**Priority system:** Transient events (low battery, mic/camera active) always override. Timer overrides music. You never see unimportant info when something critical is happening.

---

## Current Status (v1.0 Beta)

 **Fully working:**
- State transitions (IDLE → LIVE → EXPANDED)
- Spring physics animations
- Music detection via Windows SMTC
- Timer + Pomodoro
- Battery notifications
- Settings dialog
- System tray integration
- Clipboard history (10 items)
- Quick notes storage
- Customizable dimensions & font size

 **Known limitations / In development:**
- Performance optimization ongoing (smooth 60 FPS animations)
- Some edge cases in fullscreen detection
- Polish on transitions between states
- Mic/Camera detection may vary by system

---

## Setup

```bash
git clone https://github.com/your-username/dynamic-island-windows
cd dynamic-island-windows

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

**Requirements:** Python 3.9+, Windows 10/11

---

## Interactions

| Action | Result |
|---|---|
| Hover over island | Expands to LIVE (if active) |
| Short tap | Toggle LIVE ↔ EXPANDED |
| Long press (0.5 s) | Force EXPANDED |
| Right-click | Context menu with quick controls |
| Drag vertically | Reposition the island |
| Tray icon → double-click | Show island |

---

## Music detection

Reads from **Windows SMTC** (Global System Media Transport Controls) — the same API the Windows lock screen uses. Works with:

- Spotify
- Apple Music
- YouTube / SoundCloud in any browser
- Windows Media Player / Media Player (Win 11)
- Any other SMTC-integrated app

Uses `winsdk` when available, falls back to a built-in PowerShell call — no extra dependencies required for music to work.

---

## Timer / Pomodoro

Right-click the island → **Timer starten** to activate the timer widget. In EXPANDED view you can switch between Stopwatch and Countdown mode, set the duration, and start/pause/reset.

---

## Transient events

Shown automatically:
- **Battery low** (≤ 20 %) — red alert
- **Charging started** — green flash
- **Battery full** — green confirmation
- **Mic / Camera active** — orange/green dot (also from tray menu for testing)

Custom events can be pushed programmatically:
```python
island.push_event("⚡", "Ladekabel verbunden", "", "#30D158", 2500)
```

---

## Architecture

```
dynamic-island-windows/
├── main.py                  Entry point
├── island.py                Main window · state machine · spring engine
├── spring.py                Spring physics (SpringValue, SpringGroup)
├── blur.py                  Windows DWM acrylic blur via ctypes
├── activity_manager.py      Priority queue · active/inactive tracking
├── config.py                Persistent user preferences
├── styles.py                Design tokens
├── settings_dialog.py       Settings UI
├── tray.py                  System tray icon
│
├── activities/
│   ├── base.py              Abstract Activity base class
│   ├── music.py             Windows SMTC media + playback controls
│   ├── timer.py             Stopwatch + Pomodoro countdown
│   └── events.py            Transient system events (battery, mic, etc.)
│
├── panels/
│   ├── idle.py              Minimal time display + privacy dots
│   ├── live.py              Compact activity bar + split view
│   └── expanded.py          Full overlay with controls
│
└── utils/
    └── media.py             winsdk + PowerShell fallback for SMTC
```

---

## Build standalone `.exe`

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name DynamicIsland main.py
# → dist/DynamicIsland.exe
```

Push a `v1.0.0` tag to GitHub to trigger the automated release workflow.

---

## License

MIT
