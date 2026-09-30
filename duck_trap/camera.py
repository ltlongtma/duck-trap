"""Capture the intruder's photo with the webcam.

Prefers OpenCV. Falls back to `imagesnap` (macOS) when OpenCV is unavailable.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


def _timestamped_path(capture_dir: Path) -> Path:
    capture_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return capture_dir / f"duck_{stamp}.jpg"


def _capture_opencv(path: Path, camera_index: int, warmup_frames: int) -> bool:
    try:
        import cv2  # type: ignore
    except ImportError:
        return False

    cam = cv2.VideoCapture(camera_index)
    if not cam.isOpened():
        cam.release()
        return False
    try:
        # Discard the first few frames so the webcam can adjust exposure/focus.
        frame = None
        for _ in range(max(1, warmup_frames)):
            ok, f = cam.read()
            if ok:
                frame = f
            time.sleep(0.03)
        if frame is None:
            return False
        return bool(cv2.imwrite(str(path), frame))
    finally:
        cam.release()


def _capture_imagesnap(path: Path, device_name: Optional[str] = None) -> bool:
    """macOS: brew install imagesnap. Selects the camera by name if given."""
    exe = shutil.which("imagesnap")
    if not exe:
        return False
    cmd = [exe, "-w", "1"]  # -w: warm up ~1s so the shot is not dark
    if device_name:
        cmd += ["-d", device_name]
    cmd.append(str(path))
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=20)
        return path.exists()
    except (subprocess.SubprocessError, OSError):
        return False


def list_cameras() -> list[str]:
    """List macOS camera names via imagesnap (if installed)."""
    exe = shutil.which("imagesnap")
    if not exe:
        return []
    try:
        out = subprocess.run(
            [exe, "-l"], capture_output=True, text=True, timeout=15
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []
    names: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        # imagesnap prints "=> FaceTime HD Camera" or "FaceTime HD Camera".
        if not line or line.lower().startswith("video devices"):
            continue
        names.append(line.lstrip("=> ").strip())
    return names


def capture_snapshot(
    capture_dir: Path,
    camera_index: int = 0,
    warmup_frames: int = 5,
    camera_name: Optional[str] = None,
) -> Optional[Path]:
    """Take one photo; return its path on success, None on failure.

    If camera_name is given (macOS), prefer capturing with imagesnap by that
    name to avoid grabbing the iPhone camera (Continuity Camera).
    """
    path = _timestamped_path(capture_dir)

    if camera_name:
        if _capture_imagesnap(path, device_name=camera_name):
            return path
        # imagesnap failed -> still try OpenCV by index as a fallback.
        if _capture_opencv(path, camera_index, warmup_frames):
            return path
        return None

    if _capture_opencv(path, camera_index, warmup_frames):
        return path
    if _capture_imagesnap(path):
        return path
    return None
