"""Configuration for Duck Trap."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_CAPTURE_DIR = Path.home() / "DuckTrap" / "captures"


def app_dir() -> Path:
    """Directory of the running executable (when packaged with PyInstaller),
    otherwise the current working directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def _resource_dir() -> Path:
    """Directory bundled resources live in.

    Under PyInstaller, data files are unpacked to sys._MEIPASS; otherwise they
    sit next to this package.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / "duck_trap"
    return Path(__file__).resolve().parent


def bundled_default_decoy() -> Optional[Path]:
    """The decoy image shipped with the app (assets/default_decoy.png)."""
    p = _resource_dir() / "assets" / "default_decoy.png"
    return p if p.exists() else None


def find_default_decoy() -> Optional[Path]:
    """Pick the decoy image when none is given on the command line.

    1) A user image dropped next to the executable (trap.png / trap.jpg / ...)
       so a non-technical user can customize it without any command line.
    2) Otherwise the default decoy bundled with the app.
    """
    base = app_dir()
    for name in ("trap.png", "trap.jpg", "trap.jpeg", "trap.PNG", "trap.JPG"):
        p = base / name
        if p.exists():
            return p
    return bundled_default_decoy()


@dataclass
class Config:
    # Where intruder photos are saved
    capture_dir: Path = DEFAULT_CAPTURE_DIR

    # Full-screen decoy image (chosen by the user). If None, try a desktop
    # screenshot; if that fails too, draw a fake desktop.
    decoy_image_path: Optional[Path] = None

    # Silent grace period (seconds) after launch before the trap arms, so the
    # owner can step away without tripping it.
    arm_delay: float = 4.0

    # Ignore mouse movement smaller than this (pixels) to avoid false triggers
    # from hand tremor / sensor drift. Set 0 for maximum sensitivity.
    mouse_move_threshold: int = 8

    # Webcam index (0 = default camera). Used when capturing with OpenCV.
    camera_index: int = 0

    # Camera name (macOS, via imagesnap), e.g. "FaceTime HD Camera", to avoid
    # grabbing the iPhone Continuity Camera. Takes priority over camera_index.
    camera_name: Optional[str] = None

    # Number of "warm-up" frames to discard before the real shot
    # (many webcams need a few frames to auto-adjust exposure).
    camera_warmup_frames: int = 5

    # Also start a global input hook (pynput) to catch input even when the
    # window loses focus. Needs Accessibility + Input Monitoring. Off by default
    # because Tk events on the fullscreen window are enough and need no grants.
    use_global_hook: bool = False

    # Whether to auto-lock the machine after capturing
    auto_lock: bool = True

    # Whether to play a sound when the trap fires. Off by default so it runs
    # fully silently (the intruder does not know they were trapped).
    play_sound: bool = False

    # Whether to open the captures folder after the trap fires (to review it)
    open_folder_after: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Allow quick overrides via environment variables."""
        cfg = cls()
        if v := os.environ.get("DUCKTRAP_DIR"):
            cfg.capture_dir = Path(v).expanduser()
        if v := os.environ.get("DUCKTRAP_ARM_DELAY"):
            cfg.arm_delay = float(v)
        if v := os.environ.get("DUCKTRAP_CAMERA_INDEX"):
            cfg.camera_index = int(v)
        if v := os.environ.get("DUCKTRAP_CAMERA_NAME"):
            cfg.camera_name = v
        if v := os.environ.get("DUCKTRAP_IMAGE"):
            cfg.decoy_image_path = Path(v).expanduser()
        if v := os.environ.get("DUCKTRAP_NO_LOCK"):
            cfg.auto_lock = v not in ("1", "true", "yes")
        return cfg
