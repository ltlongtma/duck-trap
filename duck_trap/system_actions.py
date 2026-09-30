"""Các hành động hệ thống: khoá máy, phát tiếng, chụp màn hình nền, mở thư mục."""

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
    """Thử lần lượt các cách khoá trên macOS. Trả về (thành_công, cách_dùng)."""
    # 1) CGSession -suspend: về màn hình đăng nhập ngay (nếu bản macOS còn hỗ trợ).
    if os.path.exists(_CGSESSION) and _run_ok([_CGSESSION, "-suspend"]):
        return True, "CGSession"

    # 2) pmset displaysleepnow: tắt màn hình -> máy khoá NẾU đã bật 'require
    #    password immediately after sleep'. Không cần quyền đặc biệt.
    if shutil.which("pmset") and _run_ok(["pmset", "displaysleepnow"]):
        return True, "pmset (cần bật 'require password immediately')"

    # 3) Phím tắt khoá màn hình qua AppleScript (Control+Command+Q).
    #    Cần quyền Accessibility cho app đang chạy.
    script = (
        'tell application "System Events" to '
        'key code 12 using {control down, command down}'
    )
    if _run_ok(["osascript", "-e", script]):
        return True, "AppleScript keystroke"

    return False, "none"


def lock_screen() -> bool:
    """Khoá máy ngay lập tức. Trả về True nếu chạy được lệnh khoá."""
    if sys.platform == "darwin":
        ok, how = lock_screen_macos()
        if ok:
            print(f"[Duck Trap] Đã khoá máy bằng: {how}")
        else:
            print("[Duck Trap] ⚠️  KHÔNG khoá được máy. Thử cấp quyền "
                  "Accessibility cho app, hoặc bật 'Require password "
                  "immediately after sleep' trong System Settings.")
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
