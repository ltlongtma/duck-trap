"""Ảnh mồi (decoy) hiển thị full màn hình.

Nếu chụp được screenshot desktop thật thì dùng luôn (trông y như máy đang
mở bình thường). Nếu không, vẽ một màn hình giả trông giống desktop.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional


def load_decoy_image(root: tk.Tk, image_path: Optional[Path]):
    """Trả về PhotoImage đã scale full màn hình, hoặc None nếu không load được."""
    if not image_path or not image_path.exists():
        return None
    try:
        from PIL import Image, ImageTk  # type: ignore
    except ImportError:
        # Không có Pillow -> thử PhotoImage thuần (chỉ hỗ trợ PNG/GIF)
        try:
            return tk.PhotoImage(file=str(image_path))
        except tk.TclError:
            return None

    try:
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        img = Image.open(image_path)
        img = img.resize((sw, sh), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except (OSError, ValueError):
        return None


def build_fake_desktop(canvas: tk.Canvas, width: int, height: int) -> None:
    """Vẽ một 'desktop' giả tối giản khi không có screenshot thật."""
    canvas.configure(bg="#1e2a3a")
    # Gradient giả bằng vài dải màu
    bands = 24
    for i in range(bands):
        y0 = int(height * i / bands)
        y1 = int(height * (i + 1) / bands)
        shade = 30 + int(40 * i / bands)
        color = f"#{shade:02x}{shade + 10:02x}{shade + 25:02x}"
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline=color)

    # Thanh menu trên cùng
    canvas.create_rectangle(0, 0, width, 28, fill="#0f1620", outline="#0f1620")
    canvas.create_text(
        20, 14, anchor="w", text=" Finder   File   Edit   View",
        fill="#d8dee9", font=("Helvetica", 12),
    )
    canvas.create_text(
        width - 20, 14, anchor="e", text="Wed 3:41 PM",
        fill="#d8dee9", font=("Helvetica", 12),
    )

    # Vài "icon" file trên desktop
    for row in range(3):
        y = 70 + row * 90
        canvas.create_rectangle(
            width - 90, y, width - 40, y + 55, fill="#4c6a92", outline="#6b8cb8"
        )
        canvas.create_text(
            width - 65, y + 70, text="Untitled.pdf",
            fill="#e5ecf5", font=("Helvetica", 10),
        )
