"""System actions: lock the screen, play a sound, screenshot the desktop, open folder."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

_CGSESSION = (
    "/System/Library/CoreServices/Menu Extras/User.menu"
    "/Contents/Resources/CGSession"
)


def _run_ok(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, timeout=10, capture_output=True)
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def lock_screen_macos() -> tuple[bool, str]:
    """Try each macOS lock method in turn. Returns (success, method_used)."""
    # 1) CGSession -suspend: go straight to the login window (if this macOS
    #    version still ships it).
    if os.path.exists(_CGSESSION) and _run_ok([_CGSESSION, "-suspend"]):
        return True, "CGSession"

    # 2) pmset displaysleepnow: turn the display off -> the machine locks IF
    #    'require password immediately after sleep' is enabled. No permission.
    if shutil.which("pmset") and _run_ok(["pmset", "displaysleepnow"]):
        return True, "pmset (needs 'require password immediately')"

    # 3) Lock-screen shortcut via AppleScript (Control+Command+Q).
    #    Requires Accessibility permission for the running app.
    script = (
        'tell application "System Events" to '
        'key code 12 using {control down, command down}'
    )
    if _run_ok(["osascript", "-e", script]):
        return True, "AppleScript keystroke"

    return False, "none"


def lock_screen() -> bool:
    """Lock the machine immediately. Returns True if a lock command ran."""
    if sys.platform == "darwin":
        ok, how = lock_screen_macos()
        if ok:
            print(f"[Duck Trap] Locked the machine via: {how}")
        else:
            print("[Duck Trap] WARNING: could not lock the machine. Try granting "
                  "Accessibility to the app, or enable 'Require password "
                  "immediately after sleep' in System Settings.")
        return ok

    if sys.platform.startswith("linux"):
        for cmd in (
            ["loginctl", "lock-session"],
            ["xdg-screensaver", "lock"],
            ["gnome-screensaver-command", "-l"],
        ):
            if _run_ok(cmd):
                return True
        return False

    if sys.platform == "win32":
        return _run_ok(["rundll32.exe", "user32.dll,LockWorkStation"])

    return False


def play_alarm() -> None:
    """Play a short sound so the trap firing is audible. Non-blocking."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(
                ["afplay", "/System/Library/Sounds/Sosumi.aiff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif sys.platform == "win32":
            import winsound  # type: ignore

            winsound.MessageBeep()
        else:
            print("\a", end="", flush=True)
    except (OSError, ImportError):
        pass


def grab_desktop_screenshot(dest: Path) -> Optional[Path]:
    """Silently screenshot the current desktop to use as a realistic decoy.

    macOS only (`screencapture`). On other platforms returns None and the app
    falls back to a synthetic decoy.
    """
    if sys.platform != "darwin":
        return None
    try:
        # -x: no screenshot sound. Swallow stderr to avoid noise when Screen
        # Recording is denied (returns None -> app uses the fake desktop).
        subprocess.run(
            ["screencapture", "-x", str(dest)],
            check=True, timeout=10, capture_output=True,
        )
        return dest if dest.exists() else None
    except (subprocess.SubprocessError, OSError):
        return None


def open_folder(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        elif sys.platform == "win32":
            subprocess.Popen(["explorer", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        pass
