"""Các hành động hệ thống: khoá máy, phát tiếng, chụp màn hình nền, mở thư mục."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

_CGSESSION = (
    "/System/Library/CoreServices/Menu Extras/User.menu"
    "/Contents/Resources/CGSession"
)


def lock_screen() -> bool:
    """Khoá máy ngay lập tức. Trả về True nếu chạy được lệnh khoá."""
    if sys.platform == "darwin":
        # Cách tin cậy nhất trên macOS hiện đại: đưa về màn hình đăng nhập.
        try:
            subprocess.run([_CGSESSION, "-suspend"], check=True, timeout=10)
            return True
        except (subprocess.SubprocessError, OSError):
            pass
        # Fallback: dùng phím tắt khoá màn hình qua AppleScript (Cmd+Ctrl+Q)
        try:
            script = (
                'tell application "System Events" to '
                'key code 12 using {command down, control down}'
            )
            subprocess.run(["osascript", "-e", script], check=True, timeout=10)
            return True
        except (subprocess.SubprocessError, OSError):
            return False

    if sys.platform.startswith("linux"):
        for cmd in (
            ["loginctl", "lock-session"],
            ["xdg-screensaver", "lock"],
            ["gnome-screensaver-command", "-l"],
        ):
            try:
                subprocess.run(cmd, check=True, timeout=10)
                return True
            except (subprocess.SubprocessError, OSError):
                continue
        return False

    if sys.platform == "win32":
        try:
            subprocess.run(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                check=True,
                timeout=10,
            )
            return True
        except (subprocess.SubprocessError, OSError):
            return False

    return False


def play_alarm() -> None:
    """Phát 1 tiếng để mày (hoặc thủ phạm) biết bẫy vừa sập. Không chặn lâu."""
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
    """Chụp màn hình nền hiện tại (im lặng) để làm ảnh mồi trông y như thật.

    Chỉ hỗ trợ macOS (`screencapture`). Nền tảng khác trả về None và
    app sẽ dùng ảnh mồi giả lập.
    """
    if sys.platform != "darwin":
        return None
    try:
        # -x: không phát tiếng chụp màn hình. Nuốt stderr để khỏi rác terminal
        # khi thiếu quyền Screen Recording (khi đó trả None -> dùng desktop giả).
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
