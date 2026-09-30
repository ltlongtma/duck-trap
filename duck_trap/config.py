"""Cấu hình cho Duck Trap."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CAPTURE_DIR = Path.home() / "DuckTrap" / "captures"


@dataclass
class Config:
    # Thư mục lưu ảnh thủ phạm
    capture_dir: Path = DEFAULT_CAPTURE_DIR

    # Số giây đếm ngược sau khi bấm "arm" để mày kịp rời tay khỏi máy
    arm_delay: float = 4.0

    # Bỏ qua chuyển động chuột nhỏ hơn ngưỡng này (pixel) để tránh
    # rung tay / trôi cảm biến gây báo giả. Đặt 0 để nhạy tuyệt đối.
    mouse_move_threshold: int = 8

    # Index của webcam (0 = camera mặc định)
    camera_index: int = 0

    # Số frame "khởi động" webcam bỏ đi trước khi lấy ảnh thật
    # (nhiều webcam cần vài frame để tự chỉnh sáng)
    camera_warmup_frames: int = 5

    # Có tự khoá máy sau khi chụp không
    auto_lock: bool = True

    # Có phát tiếng "bíp" khi sập bẫy không
    play_sound: bool = True

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
        if v := os.environ.get("DUCKTRAP_NO_LOCK"):
            cfg.auto_lock = v not in ("1", "true", "yes")
        return cfg
