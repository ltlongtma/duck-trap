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


def _capture_imagesnap(path: Path, device_name: Optional[str] = None) -> bool:
    """macOS: brew install imagesnap. Chọn camera theo tên nếu có."""
    exe = shutil.which("imagesnap")
    if not exe:
        return False
    cmd = [exe, "-w", "1"]  # -w: chờ camera chỉnh sáng ~1s cho ảnh không tối
    if device_name:
        cmd += ["-d", device_name]
    cmd.append(str(path))
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=20)
        return path.exists()
    except (subprocess.SubprocessError, OSError):
        return False


def list_cameras() -> list[str]:
    """Liệt kê tên các camera macOS qua imagesnap (nếu có)."""
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
        # imagesnap in dạng: "=> FaceTime HD Camera" hoặc "FaceTime HD Camera"
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
    """Chụp 1 ảnh, trả về đường dẫn nếu thành công, None nếu thất bại.

    Nếu chỉ định camera_name (macOS) thì ưu tiên chụp bằng imagesnap theo
    tên đó để tránh bị vớ nhầm camera iPhone (Continuity Camera).
    """
    path = _timestamped_path(capture_dir)

    if camera_name:
        if _capture_imagesnap(path, device_name=camera_name):
            return path
        # imagesnap fail -> vẫn thử OpenCV theo index cho chắc
        if _capture_opencv(path, camera_index, warmup_frames):
            return path
        return None

    if _capture_opencv(path, camera_index, warmup_frames):
        return path
    if _capture_imagesnap(path):
        return path
    return None
