"""Duck Trap core: decoy screen + touch detection + response."""

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
        self._decoy_image = None  # keep a ref so it is not garbage-collected
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

    # ---- lifecycle ---------------------------------------------------

    def run(self) -> None:
        self._go_fullscreen()
        # Show the decoy immediately so it looks like a normal screen (no countdown).
        self._show_decoy()
        # ESC lets the OWNER cancel during the silent grace period, before arming.
        self.root.bind("<Escape>", lambda e: self._abort())
        # Silent grace period: enough for the owner to step away, so the launch
        # keystroke/mouse move does not trip the trap. Nothing is shown.
        self.root.after(int(self.cfg.arm_delay * 1000), self._activate_trap)
        self.root.mainloop()

    def _go_fullscreen(self) -> None:
        # Native fullscreen (Tk 8.6): the window stays a "key window" so it
        # receives keyboard events -> Tk events catch keystrokes with no special
        # permission. (No overrideredirect: on macOS it blocks key focus.)
        self.root.geometry(f"{self._screen_w}x{self._screen_h}+0+0")
        self.root.attributes("-topmost", True)
        try:
            self.root.config(cursor="none")
        except tk.TclError:
            pass
        # Apply -fullscreen after the window is mapped so it reliably engages.
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
        # The decoy is already shown from run(); make sure we hold focus (so a
        # stray FocusOut doesn't fire the moment we arm), then anchor the
        # pointer baseline and arm.
        self.root.lift()
        self.root.focus_force()
        self.root.update_idletasks()
        self._baseline_pointer = self._pointer_now()
        self._start_input_listener()
        self._armed = True

    def _show_decoy(self) -> None:
        # Decoy image priority:
        #   1) A user-provided image (--image / trap.png next to the app)
        #   2) A real desktop screenshot (needs Screen Recording permission)
        #   3) A minimal fake desktop
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
        # Remove the temporary screenshot (the image already lives in Tk memory).
        try:
            if temp_shot and temp_shot.exists():
                temp_shot.unlink()
        except OSError:
            pass

    # ---- touch detection ---------------------------------------------

    def _pointer_now(self) -> tuple[int, int]:
        return (self.root.winfo_pointerx(), self.root.winfo_pointery())

    def _start_input_listener(self) -> None:
        # ALWAYS bind Tk events: the window is fullscreen and holds focus, so
        # every key/mouse/touchpad action goes to it and is caught WITHOUT any
        # Accessibility permission. This is the primary detection layer.
        self.root.bind_all("<Key>", lambda e: self._trigger("key press"))
        self.root.bind_all("<Button>", lambda e: self._trigger("mouse/touchpad"))
        self.root.bind_all("<Motion>", self._tk_motion)

        # Escaping the trap counts as a trigger too. Mission Control (4-finger
        # swipe up), switching Spaces (swipe left/right) and Cmd+Tab are
        # swallowed by the system, so they never arrive as key/mouse events --
        # instead our window loses focus / the app is deactivated. Treat that as
        # someone trying to get out: snap + lock.
        self.root.bind("<Deactivate>", lambda e: self._trigger("app switch / Mission Control"))
        self.root.bind("<FocusOut>", lambda e: self._trigger("lost focus"))

        # Optional: also start a global hook (pynput) to catch input even without
        # focus. Needs Accessibility + Input Monitoring; if not granted it errors,
        # which we swallow and keep running on the Tk events above.
        if self.cfg.use_global_hook:
            self._start_global_hook()

    def _start_global_hook(self) -> None:
        try:
            from pynput import keyboard, mouse  # type: ignore
        except ImportError:
            print("[Duck Trap] pynput not available; using Tk events.")
            return

        def on_key(_key):
            self._trigger("key press (global)")

        def on_click(_x, _y, _button, pressed):
            if pressed:
                self._trigger("click (global)")

        def on_move(x, y):
            if self._baseline_pointer is None:
                return
            bx, by = self._baseline_pointer
            if abs(x - bx) + abs(y - by) >= self.cfg.mouse_move_threshold:
                self._trigger("mouse move (global)")

        try:
            self._kb_listener = keyboard.Listener(on_press=on_key)
            self._ms_listener = mouse.Listener(on_click=on_click, on_move=on_move)
            self._kb_listener.start()
            self._ms_listener.start()
        except Exception as exc:  # noqa: BLE001 - permission/backend errors vary
            print(f"[Duck Trap] Global hook could not start ({exc}). "
                  "Grant Accessibility + Input Monitoring. "
                  "Continuing with Tk events.")

    def _tk_motion(self, event) -> None:
        if self._baseline_pointer is None:
            return
        bx, by = self._baseline_pointer
        if abs(event.x_root - bx) + abs(event.y_root - by) >= self.cfg.mouse_move_threshold:
            self._trigger("mouse/touchpad move")

    # ---- response when the trap fires --------------------------------

    def _trigger(self, reason: str) -> None:
        with self._lock:
            if not self._armed or self._fired:
                return
            self._fired = True

        # Run the response on its own thread so the callback is not blocked.
        threading.Thread(
            target=self._respond, args=(reason,), daemon=True
        ).start()

    def _respond(self, reason: str) -> None:
        self._stop_listeners()

        if self.cfg.play_sound:
            sysact.play_alarm()

        # Capture the intruder's photo BEFORE locking (the camera may turn off
        # once the machine locks).
        photo = capture_snapshot(
            self.cfg.capture_dir,
            camera_index=self.cfg.camera_index,
            warmup_frames=self.cfg.camera_warmup_frames,
            camera_name=self.cfg.camera_name,
        )

        # Lock the machine SILENTLY: no message, no screen change, no sound.
        # The intruder just sees the machine "lock itself" as usual.
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
        # Print the result to the terminal for when the owner returns.
        if photo is not None:
            print(f"[Duck Trap] Gotcha! Photo saved to: {photo}")
        else:
            print("[Duck Trap] Trap fired but NO photo was captured "
                  "(check Camera permission / install opencv-python or imagesnap).")

    # ---- cancel / cleanup --------------------------------------------

    def _abort(self) -> None:
        if self._armed:
            return  # once armed, ESC will not save the intruder :)
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
