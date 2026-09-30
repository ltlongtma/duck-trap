"""Cấu hình cho Duck Trap."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_CAPTURE_DIR = Path.home() / "DuckTrap" / "captures"


def app_dir() -> Path:
    """Thư mục chứa file chạy (khi đóng gói bằng PyInstaller) hoặc cwd."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def find_default_decoy() -> Optional[Path]:
    """Tự tìm ảnh mồi đặt cạnh file chạy: trap.png / trap.jpg / trap.jpeg.

    Giúp người non-tech chỉ cần bỏ 1 ảnh tên 'trap.png' cạnh app rồi
    double-click, khỏi cần gõ lệnh.
    """
    base = app_dir()
    for name in ("trap.png", "trap.jpg", "trap.jpeg", "trap.PNG", "trap.JPG"):
        p = base / name
        if p.exists():
            return p
    return None


@dataclass
class Config:
    # Thư mục lưu ảnh thủ phạm
    capture_dir: Path = DEFAULT_CAPTURE_DIR

    # Ảnh mồi hiển thị full màn hình (do mày tự chọn). Nếu None -> thử
    # chụp screenshot desktop; nếu vẫn không được -> vẽ desktop giả.
    decoy_image_path: Optional[Path] = None

    # Số giây đếm ngược sau khi bấm "arm" để mày kịp rời tay khỏi máy
    arm_delay: float = 4.0

    # Bỏ qua chuyển động chuột nhỏ hơn ngưỡng này (pixel) để tránh
    # rung tay / trôi cảm biến gây báo giả. Đặt 0 để nhạy tuyệt đối.
    mouse_move_threshold: int = 8

    # Index của webcam (0 = camera mặc định). Dùng khi chụp bằng OpenCV.
    camera_index: int = 0

    # Tên camera (macOS, qua imagesnap). Vd "FaceTime HD Camera" để tránh
    # bị vớ nhầm camera iPhone (Continuity Camera). Ưu tiên hơn camera_index.
    camera_name: Optional[str] = None

    # Số frame "khởi động" webcam bỏ đi trước khi lấy ảnh thật
    # (nhiều webcam cần vài frame để tự chỉnh sáng)
    camera_warmup_frames: int = 5

    # Bật thêm global hook (pynput) để bắt input cả khi cửa sổ không có focus.
    # Cần quyền Accessibility + Input Monitoring. Mặc định tắt vì Tk-events
    # trên cửa sổ fullscreen đã đủ và không cần cấp quyền.
    use_global_hook: bool = False

    # Có tự khoá máy sau khi chụp không
    auto_lock: bool = True

    # Có phát tiếng khi sập bẫy không. Mặc định TẮT để chạy hoàn toàn âm thầm
    # (thủ phạm không biết mình bị bẫy).
    play_sound: bool = False

    # Có tự mở thư mục ảnh sau khi sập bẫy không (để mày xem ngay)
    open_folder_after: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Cho phép override nhanh qua biến môi trường."""
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
