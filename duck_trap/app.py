"""Duck Trap - lõi ứng dụng: màn hình mồi + phát hiện chạm + phản ứng."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from typing import Optional

from .camera import capture_snapshot
from .config import Config
from . import decoy
from . import system_actions as sysact


class DuckTrapApp:
    def __init__(self, config: Config):
        self.cfg = config
        self.root = tk.Tk()
        self.root.title("Duck Trap")

        self._armed = False
        self._fired = False
        self._lock = threading.Lock()

        self._baseline_pointer: Optional[tuple[int, int]] = None
        self._decoy_image = None  # giữ ref để khỏi bị GC
        self._listener = None

        self._screen_w = self.root.winfo_screenwidth()
        self._screen_h = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(
            self.root,
            width=self._screen_w,
            height=self._screen_h,
            highlightthickness=0,
            bg="black",
        )
        self.canvas.pack(fill="both", expand=True)

        self._status_text = self.canvas.create_text(
            self._screen_w // 2,
            self._screen_h // 2,
            text="",
            fill="#ffffff",
            font=("Helvetica", 42, "bold"),
        )

    # ---- vòng đời ----------------------------------------------------

    def run(self) -> None:
        self._go_fullscreen()
        # Cho phép ESC thoát trong lúc còn đếm ngược (chỉ mày biết).
        self.root.bind("<Escape>", lambda e: self._abort())
        self.root.after(100, self._arm_countdown, self.cfg.arm_delay)
        self.root.mainloop()

    def _go_fullscreen(self) -> None:
        # Che kín màn hình, bỏ thanh tiêu đề. Dùng cả overrideredirect +
        # geometry (đáng tin trên macOS) lẫn -fullscreen.
        self.root.overrideredirect(True)
        self.root.geometry(f"{self._screen_w}x{self._screen_h}+0+0")
        try:
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            pass
        self.root.attributes("-topmost", True)
        try:
            self.root.config(cursor="none")
        except tk.TclError:
            pass
        self.root.lift()
        self.root.focus_force()
        self.root.update_idletasks()

    # ---- arming ------------------------------------------------------

    def _arm_countdown(self, remaining: float) -> None:
        if remaining > 0:
            secs = int(remaining + 0.999)
            self.canvas.itemconfigure(
                self._status_text,
                text=f"Duck Trap sẽ vũ trang sau {secs}…\n(ESC để huỷ)",
            )
            self.root.after(200, self._arm_countdown, remaining - 0.2)
            return
        self._activate_trap()

    def _activate_trap(self) -> None:
        # Chụp desktop thật để làm ảnh mồi, rồi hiển thị full màn hình.
        self._show_decoy()
        self._baseline_pointer = self._pointer_now()
        self._start_input_listener()
        self._armed = True

    def _show_decoy(self) -> None:
        # Thứ tự ưu tiên ảnh mồi:
        #   1) Ảnh do mày tự chọn (--image)
        #   2) Screenshot desktop thật (cần quyền Screen Recording)
        #   3) Vẽ desktop giả tối giản
        self._decoy_image = None
        temp_shot: Optional[Path] = None

        if self.cfg.decoy_image_path and self.cfg.decoy_image_path.exists():
            self._decoy_image = decoy.load_decoy_image(
                self.root, self.cfg.decoy_image_path
            )

        if self._decoy_image is None:
            temp_shot = self.cfg.capture_dir / ".decoy.png"
            real = sysact.grab_desktop_screenshot(temp_shot)
            self._decoy_image = decoy.load_decoy_image(self.root, real)

        self.canvas.delete("all")
        if self._decoy_image is not None:
            self.canvas.create_image(
                0, 0, anchor="nw", image=self._decoy_image
            )
        else:
            decoy.build_fake_desktop(
                self.canvas, self._screen_w, self._screen_h
            )
        # xoá screenshot tạm (ảnh đã nằm trong bộ nhớ Tk)
        try:
            if temp_shot and temp_shot.exists():
                temp_shot.unlink()
        except OSError:
            pass

    # ---- phát hiện chạm ---------------------------------------------

    def _pointer_now(self) -> tuple[int, int]:
        return (self.root.winfo_pointerx(), self.root.winfo_pointery())

    def _start_input_listener(self) -> None:
        try:
            from pynput import keyboard, mouse  # type: ignore
        except ImportError:
            # Không có pynput: dựa vào sự kiện Tk (kém nhạy hơn với touchpad
            # khi cửa sổ không giữ focus, nhưng vẫn bắt được phím/click).
            self.root.bind_all("<Key>", lambda e: self._trigger("phím bấm"))
            self.root.bind_all("<Button>", lambda e: self._trigger("chuột/touchpad"))
            self.root.bind_all("<Motion>", self._tk_motion)
            return

        def on_key(_key):
            self._trigger("phím bấm")

        def on_click(_x, _y, _button, pressed):
            if pressed:
                self._trigger("click chuột/touchpad")

        def on_move(x, y):
            if self._baseline_pointer is None:
                return
            bx, by = self._baseline_pointer
            if abs(x - bx) + abs(y - by) >= self.cfg.mouse_move_threshold:
                self._trigger("di chuột/touchpad")

        self._kb_listener = keyboard.Listener(on_press=on_key)
        self._ms_listener = mouse.Listener(on_click=on_click, on_move=on_move)
        self._kb_listener.start()
        self._ms_listener.start()

    def _tk_motion(self, event) -> None:
        if self._baseline_pointer is None:
            return
        bx, by = self._baseline_pointer
        if abs(event.x_root - bx) + abs(event.y_root - by) >= self.cfg.mouse_move_threshold:
            self._trigger("di chuột/touchpad")

    # ---- phản ứng khi sập bẫy ---------------------------------------

    def _trigger(self, reason: str) -> None:
        with self._lock:
            if not self._armed or self._fired:
                return
            self._fired = True

        # Chạy chuỗi phản ứng ở thread riêng để không kẹt callback.
        threading.Thread(
            target=self._respond, args=(reason,), daemon=True
        ).start()

    def _respond(self, reason: str) -> None:
        self._stop_listeners()

        if self.cfg.play_sound:
            sysact.play_alarm()

        # 1) CHỤP ẢNH thủ phạm TRƯỚC khi khoá (khoá xong camera có thể tắt).
        photo = capture_snapshot(
            self.cfg.capture_dir,
            camera_index=self.cfg.camera_index,
            warmup_frames=self.cfg.camera_warmup_frames,
            camera_name=self.cfg.camera_name,
        )

        # 2) Báo "GOTCHA" chớp nhoáng rồi khoá máy.
        self.root.after(0, self._flash_gotcha, reason, photo)

    def _flash_gotcha(self, reason: str, photo: Optional[Path]) -> None:
        self.canvas.delete("all")
        self.canvas.configure(bg="#7a0000")
        msg = "🦆  GOTCHA!  🦆\nĐừng duck máy người khác nữa nhé"
        self.canvas.create_text(
            self._screen_w // 2,
            self._screen_h // 2,
            text=msg,
            fill="#ffffff",
            font=("Helvetica", 48, "bold"),
            justify="center",
        )
        self.root.update_idletasks()
        # Giữ màn hình đỏ ~1.2s cho thủ phạm đọc kịp rồi khoá.
        self.root.after(1200, self._finish, photo)

    def _finish(self, photo: Optional[Path]) -> None:
        if self.cfg.auto_lock:
            sysact.lock_screen()
        if self.cfg.open_folder_after and photo is not None:
            sysact.open_folder(self.cfg.capture_dir)
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        # In ra terminal cho mày biết kết quả khi mở lại máy.
        if photo is not None:
            print(f"[Duck Trap] Đã tóm được! Ảnh lưu tại: {photo}")
        else:
            print("[Duck Trap] Bẫy đã sập nhưng KHÔNG chụp được ảnh "
                  "(kiểm tra quyền Camera / cài opencv-python hoặc imagesnap).")

    # ---- huỷ / dọn dẹp ----------------------------------------------

    def _abort(self) -> None:
        if self._armed:
            return  # đã vũ trang thì ESC không cứu được thủ phạm :)
        self._stop_listeners()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _stop_listeners(self) -> None:
        for name in ("_kb_listener", "_ms_listener"):
            listener = getattr(self, name, None)
            if listener is not None:
                try:
                    listener.stop()
                except Exception:
                    pass
