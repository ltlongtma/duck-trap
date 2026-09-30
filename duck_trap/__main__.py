"""Điểm chạy: python -m duck_trap"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .app import DuckTrapApp
from .config import Config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="duck_trap",
        description="Bẫy tóm kẻ đi 'duck' máy: chạm vào là chụp ảnh + khoá máy.",
    )
    p.add_argument(
        "--dir", type=Path, default=None,
        help="Thư mục lưu ảnh (mặc định ~/DuckTrap/captures).",
    )
    p.add_argument(
        "--arm-delay", type=float, default=None,
        help="Số giây đếm ngược trước khi vũ trang (mặc định 4).",
    )
    p.add_argument(
        "--camera", type=int, default=None,
        help="Index webcam (mặc định 0).",
    )
    p.add_argument(
        "--sensitivity", type=int, default=None,
        help="Ngưỡng di chuột (pixel) để tính là bị chạm. Nhỏ = nhạy hơn.",
    )
    p.add_argument(
        "--no-lock", action="store_true",
        help="Chỉ chụp ảnh, KHÔNG tự khoá máy (dùng để test).",
    )
    p.add_argument(
        "--no-sound", action="store_true",
        help="Không phát tiếng khi sập bẫy.",
    )
    p.add_argument(
        "--open-folder", action="store_true",
        help="Tự mở thư mục ảnh sau khi sập bẫy.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    cfg = Config.from_env()
    if args.dir is not None:
        cfg.capture_dir = args.dir.expanduser()
    if args.arm_delay is not None:
        cfg.arm_delay = args.arm_delay
    if args.camera is not None:
        cfg.camera_index = args.camera
    if args.sensitivity is not None:
        cfg.mouse_move_threshold = args.sensitivity
    if args.no_lock:
        cfg.auto_lock = False
    if args.no_sound:
        cfg.play_sound = False
    if args.open_folder:
        cfg.open_folder_after = True

    cfg.capture_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 56)
    print(" 🦆  DUCK TRAP đang vũ trang…")
    print(f"     Ảnh sẽ lưu tại: {cfg.capture_dir}")
    print(f"     Tự khoá máy: {'CÓ' if cfg.auto_lock else 'KHÔNG'}")
    print("     Nhấn ESC trong lúc đếm ngược để huỷ.")
    print("=" * 56)

    try:
        DuckTrapApp(cfg).run()
    except KeyboardInterrupt:
        print("\n[Duck Trap] Đã huỷ.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
