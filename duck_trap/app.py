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

    # ---- vòng đời ----------------------------------------------------

    def run(self) -> None:
        self._go_fullscreen()
        # Hiện ảnh mồi NGAY để trông như màn hình bình thường (không countdown).
        self._show_decoy()
        # ESC chỉ để CHỦ MÁY huỷ trong khoảng ân hạn im lặng trước khi vũ trang.
        self.root.bind("<Escape>", lambda e: self._abort())
        # Ân hạn im lặng: đủ để chủ máy rời tay, tránh tự sập bẫy vì cú bấm/di
        # chuột lúc khởi động. KHÔNG hiển thị gì cả.
        self.root.after(int(self.cfg.arm_delay * 1000), self._activate_trap)
        self.root.mainloop()

    def _go_fullscreen(self) -> None:
        # Native fullscreen (Tk 8.6): cửa sổ vẫn là "key window" nên nhận được
        # sự kiện bàn phím -> Tk-events bắt được phím mà không cần quyền gì.
        # (KHÔNG dùng overrideredirect vì trên macOS nó chặn nhận phím.)
        self.root.geometry(f"{self._screen_w}x{self._screen_h}+0+0")
        self.root.attributes("-topmost", True)
        try:
            self.root.config(cursor="none")
        except tk.TclError:
            pass
        # Áp -fullscreen sau khi cửa sổ đã hiển thị để chắc chắn ăn.
        self.root.after(60, self._engage_fullscreen)

    def _engage_fullscreen(self) -> None:
        try:
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            pass
        self.root.lift()
        self.root.focus_force()
        self.root.update_idletasks()

    # ---- arming ------------------------------------------------------

    def _activate_trap(self) -> None:
        # Ảnh mồi đã hiện sẵn từ run(); giờ chỉ chốt mốc chuột rồi vũ trang.
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
        # LUÔN bind event của Tkinter: cửa sổ đang fullscreen + giữ focus nên
        # mọi phím/chuột/touchpad hướng vào máy đều được bắt, KHÔNG cần cấp
        # quyền Accessibility. Đây là lớp phát hiện chính.
        self.root.bind_all("<Key>", lambda e: self._trigger("phím bấm"))
        self.root.bind_all("<Button>", lambda e: self._trigger("chuột/touchpad"))
        self.root.bind_all("<Motion>", self._tk_motion)

        # Tùy chọn: bật thêm global hook (pynput) để bắt cả khi không có focus.
        # Cần quyền Accessibility + Input Monitoring; nếu chưa cấp sẽ báo lỗi,
        # ta nuốt gọn và vẫn chạy bằng Tk-events ở trên.
        if self.cfg.use_global_hook:
            self._start_global_hook()

    def _start_global_hook(self) -> None:
        try:
            from pynput import keyboard, mouse  # type: ignore
        except ImportError:
            print("[Duck Trap] Không có pynput; dùng Tk-events.")
            return

        def on_key(_key):
            self._trigger("phím bấm (global)")

        def on_click(_x, _y, _button, pressed):
            if pressed:
                self._trigger("click (global)")

        def on_move(x, y):
            if self._baseline_pointer is None:
                return
            bx, by = self._baseline_pointer
            if abs(x - bx) + abs(y - by) >= self.cfg.mouse_move_threshold:
                self._trigger("di chuột (global)")

        try:
            self._kb_listener = keyboard.Listener(on_press=on_key)
            self._ms_listener = mouse.Listener(on_click=on_click, on_move=on_move)
            self._kb_listener.start()
            self._ms_listener.start()
        except Exception as exc:  # noqa: BLE001 - permission/backend lỗi đủ kiểu
            print(f"[Duck Trap] Global hook không bật được ({exc}). "
                  "Cần cấp quyền Accessibility + Input Monitoring. "
                  "Vẫn chạy bằng Tk-events.")

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

        # Chụp ảnh thủ phạm TRƯỚC khi khoá (khoá xong camera có thể tắt).
        photo = capture_snapshot(
            self.cfg.capture_dir,
            camera_index=self.cfg.camera_index,
            warmup_frames=self.cfg.camera_warmup_frames,
            camera_name=self.cfg.camera_name,
        )

        # Khoá máy ÂM THẦM ngay: không báo, không đổi màn hình, không tiếng.
        # Thủ phạm chỉ thấy máy "tự khoá" như bình thường.
        self.root.after(0, self._finish, photo)

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
