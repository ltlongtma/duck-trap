"""Entry point: python -m duck_trap"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .app import DuckTrapApp
from .config import Config, find_default_decoy


def _ensure_std_streams() -> None:
    """The windowed packaged build has no console, so sys.stdout/err can be
    None and print() would fail. Redirect to devnull to be safe."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="duck_trap",
        description="Trap for machine pranksters: on touch, snap a photo + lock.",
    )
    p.add_argument(
        "--dir", type=Path, default=None,
        help="Folder to save photos (default ~/DuckTrap/captures).",
    )
    p.add_argument(
        "--arm-delay", type=float, default=None,
        help="Silent grace period in seconds before arming (default 4).",
    )
    p.add_argument(
        "--image", type=Path, default=None,
        help="Custom full-screen decoy image (PNG/JPG).",
    )
    p.add_argument(
        "--camera", type=int, default=None,
        help="Webcam index (default 0).",
    )
    p.add_argument(
        "--camera-name", type=str, default=None,
        help='macOS camera name, e.g. "MacBook Pro Camera", to avoid grabbing '
             "the iPhone camera (Continuity Camera). Takes priority over --camera.",
    )
    p.add_argument(
        "--list-cameras", action="store_true",
        help="List camera names and exit (needs imagesnap).",
    )
    p.add_argument(
        "--test-lock", action="store_true",
        help="Try locking the machine now to verify it works, then exit.",
    )
    p.add_argument(
        "--sensitivity", type=int, default=None,
        help="Mouse-move threshold (pixels) counted as a touch. Lower = more sensitive.",
    )
    p.add_argument(
        "--global-hook", action="store_true",
        help="Also start a global input hook (pynput) to catch input even when "
             "the window loses focus. Needs Accessibility + Input Monitoring.",
    )
    p.add_argument(
        "--no-lock", action="store_true",
        help="Only capture a photo, do NOT lock the machine (for testing).",
    )
    p.add_argument(
        "--sound", action="store_true",
        help="Play a sound when the trap fires (default SILENT).",
    )
    p.add_argument(
        "--open-folder", action="store_true",
        help="Open the captures folder after the trap fires.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    _ensure_std_streams()
    args = build_parser().parse_args(argv)

    if args.test_lock:
        from . import system_actions
        import time
        print("[Duck Trap] Locking the machine in 2 seconds...")
        time.sleep(2)
        ok = system_actions.lock_screen()
        return 0 if ok else 1

    if args.list_cameras:
        from .camera import list_cameras
        cams = list_cameras()
        if cams:
            print('Cameras found (use with --camera-name "<name>"):')
            for name in cams:
                print(f"  - {name}")
        else:
            print("Could not list cameras. Install imagesnap: brew install imagesnap")
        return 0

    cfg = Config.from_env()
    if args.dir is not None:
        cfg.capture_dir = args.dir.expanduser()
    if args.image is not None:
        cfg.decoy_image_path = args.image.expanduser()
    elif cfg.decoy_image_path is None:
        # No image given -> auto-find trap.png/jpg next to the app (non-tech).
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
        print(f"[Duck Trap] WARNING: decoy image not found: {cfg.decoy_image_path}")
        print("            Falling back to a desktop screenshot / fake desktop.")

    if cfg.decoy_image_path and cfg.decoy_image_path.exists():
        decoy_src = str(cfg.decoy_image_path)
    else:
        decoy_src = "desktop screenshot / fake desktop"

    cam_src = cfg.camera_name or f"index {cfg.camera_index}"

    print("=" * 56)
    print(" DUCK TRAP is arming...")
    print(f"     Decoy:      {decoy_src}")
    print(f"     Camera:     {cam_src}")
    print(f"     Photos:     {cfg.capture_dir}")
    print(f"     Auto-lock:  {'ON' if cfg.auto_lock else 'OFF'}")
    print("     Press ESC during the grace period to cancel.")
    print("=" * 56)

    try:
        DuckTrapApp(cfg).run()
    except KeyboardInterrupt:
        print("\n[Duck Trap] Cancelled.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
