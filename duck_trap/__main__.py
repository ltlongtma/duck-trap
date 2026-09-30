"""Điểm chạy: python -m duck_trap"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .app import DuckTrapApp
from .config import Config, find_default_decoy


def _ensure_std_streams() -> None:
    """Bản đóng gói windowed không có console -> sys.stdout/err có thể là None,
    khiến print() lỗi. Chuyển hướng về devnull cho an toàn."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


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
        "--image", type=Path, default=None,
        help="Ảnh mồi tự chọn để hiển thị full màn hình (PNG/JPG).",
    )
    p.add_argument(
        "--camera", type=int, default=None,
        help="Index webcam (mặc định 0).",
    )
    p.add_argument(
        "--camera-name", type=str, default=None,
        help='Tên camera macOS, vd "FaceTime HD Camera", để tránh vớ nhầm '
             "camera iPhone (Continuity Camera). Ưu tiên hơn --camera.",
    )
    p.add_argument(
        "--list-cameras", action="store_true",
        help="Liệt kê tên các camera rồi thoát (cần imagesnap).",
    )
    p.add_argument(
        "--test-lock", action="store_true",
        help="Thử khoá máy ngay để kiểm tra, rồi thoát.",
    )
    p.add_argument(
        "--sensitivity", type=int, default=None,
        help="Ngưỡng di chuột (pixel) để tính là bị chạm. Nhỏ = nhạy hơn.",
    )
    p.add_argument(
        "--global-hook", action="store_true",
        help="Bật thêm global input hook (pynput) để bắt cả khi cửa sổ không "
             "có focus. Cần quyền Accessibility + Input Monitoring.",
    )
    p.add_argument(
        "--no-lock", action="store_true",
        help="Chỉ chụp ảnh, KHÔNG tự khoá máy (dùng để test).",
    )
    p.add_argument(
        "--sound", action="store_true",
        help="Phát tiếng khi sập bẫy (mặc định IM LẶNG).",
    )
    p.add_argument(
        "--open-folder", action="store_true",
        help="Tự mở thư mục ảnh sau khi sập bẫy.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    _ensure_std_streams()
    args = build_parser().parse_args(argv)

    if args.test_lock:
        from . import system_actions
        print("[Duck Trap] Thử khoá máy trong 2 giây…")
        import time
        time.sleep(2)
        ok = system_actions.lock_screen()
        return 0 if ok else 1

    if args.list_cameras:
        from .camera import list_cameras
        cams = list_cameras()
        if cams:
            print("Camera tìm thấy (dùng với --camera-name \"<tên>\"):")
            for name in cams:
                print(f"  • {name}")
        else:
            print("Không liệt kê được camera. Cài imagesnap: brew install imagesnap")
        return 0

    cfg = Config.from_env()
    if args.dir is not None:
        cfg.capture_dir = args.dir.expanduser()
    if args.image is not None:
        cfg.decoy_image_path = args.image.expanduser()
    elif cfg.decoy_image_path is None:
        # Không chỉ định ảnh -> tự tìm trap.png/jpg đặt cạnh app (non-tech).
        cfg.decoy_image_path = find_default_decoy()
    if args.arm_delay is not None:
        cfg.arm_delay = args.arm_delay
    if args.camera is not None:
        cfg.camera_index = args.camera
    if args.camera_name is not None:
        cfg.camera_name = args.camera_name
    if args.sensitivity is not None:
        cfg.mouse_move_threshold = args.sensitivity
    if args.global_hook:
        cfg.use_global_hook = True
    if args.no_lock:
        cfg.auto_lock = False
    if args.sound:
        cfg.play_sound = True
    if args.open_folder:
        cfg.open_folder_after = True

    cfg.capture_dir.mkdir(parents=True, exist_ok=True)

    if cfg.decoy_image_path and not cfg.decoy_image_path.exists():
        print(f"[Duck Trap] ⚠️  Không thấy ảnh mồi: {cfg.decoy_image_path}")
        print("            Sẽ dùng screenshot desktop / desktop giả thay thế.")

    if cfg.decoy_image_path and cfg.decoy_image_path.exists():
        decoy_src = str(cfg.decoy_image_path)
    else:
        decoy_src = "screenshot desktop / desktop giả"

    cam_src = cfg.camera_name or f"index {cfg.camera_index}"

    print("=" * 56)
    print(" 🦆  DUCK TRAP đang vũ trang…")
    print(f"     Ảnh mồi:     {decoy_src}")
    print(f"     Camera:      {cam_src}")
    print(f"     Ảnh lưu tại: {cfg.capture_dir}")
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
