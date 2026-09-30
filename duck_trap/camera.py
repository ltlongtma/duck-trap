"""Chụp ảnh thủ phạm bằng webcam.

Ưu tiên OpenCV. Nếu không có OpenCV, fallback sang `imagesnap` (macOS).
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
        # Bỏ vài frame đầu để webcam kịp chỉnh sáng/nét
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


def _capture_imagesnap(path: Path) -> bool:
    """Fallback macOS: brew install imagesnap."""
    exe = shutil.which("imagesnap")
    if not exe:
        return False
    try:
        # -w: chờ camera chỉnh sáng ~1s cho ảnh không tối thui
        subprocess.run(
            [exe, "-w", "1", str(path)],
            check=True,
            capture_output=True,
            timeout=15,
        )
        return path.exists()
    except (subprocess.SubprocessError, OSError):
        return False


def capture_snapshot(
    capture_dir: Path,
    camera_index: int = 0,
    warmup_frames: int = 5,
) -> Optional[Path]:
    """Chụp 1 ảnh, trả về đường dẫn nếu thành công, None nếu thất bại."""
    path = _timestamped_path(capture_dir)

    if _capture_opencv(path, camera_index, warmup_frames):
        return path
    if _capture_imagesnap(path):
        return path
    return None
