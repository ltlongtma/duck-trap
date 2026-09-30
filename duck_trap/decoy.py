"""Full-screen decoy image.

If a real desktop screenshot is available, use it (looks like the machine is
open as usual). Otherwise draw a fake screen that resembles a desktop.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional


def load_decoy_image(root: tk.Tk, image_path: Optional[Path]):
    """Return a PhotoImage scaled to the full screen, or None if it can't load."""
    if not image_path or not image_path.exists():
        return None
    try:
        from PIL import Image, ImageTk  # type: ignore
    except ImportError:
        # No Pillow -> try plain PhotoImage (PNG/GIF only).
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
    """Draw a minimal fake 'desktop' when no real screenshot is available."""
    canvas.configure(bg="#1e2a3a")
    # Fake gradient made of a few color bands.
    bands = 24
    for i in range(bands):
        y0 = int(height * i / bands)
        y1 = int(height * (i + 1) / bands)
        shade = 30 + int(40 * i / bands)
        color = f"#{shade:02x}{shade + 10:02x}{shade + 25:02x}"
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline=color)

    # Top menu bar
    canvas.create_rectangle(0, 0, width, 28, fill="#0f1620", outline="#0f1620")
    canvas.create_text(
        20, 14, anchor="w", text=" Finder   File   Edit   View",
        fill="#d8dee9", font=("Helvetica", 12),
    )
    canvas.create_text(
        width - 20, 14, anchor="e", text="Wed 3:41 PM",
        fill="#d8dee9", font=("Helvetica", 12),
    )

    # A few file "icons" on the desktop
    for row in range(3):
        y = 70 + row * 90
        canvas.create_rectangle(
            width - 90, y, width - 40, y + 55, fill="#4c6a92", outline="#6b8cb8"
        )
        canvas.create_text(
            width - 65, y + 70, text="Untitled.pdf",
            fill="#e5ecf5", font=("Helvetica", 10),
        )
