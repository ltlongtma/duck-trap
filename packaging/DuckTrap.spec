# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec cho Duck Trap (chạy trên Windows lẫn macOS).

Build:
    pip install pyinstaller
    pyinstaller packaging/DuckTrap.spec --noconfirm
Kết quả nằm ở dist/DuckTrap.exe (Windows) hoặc dist/DuckTrap.app (macOS).
"""

import sys

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Thu gom đầy đủ opencv (cv2) để khỏi thiếu binary khi chạy bản đóng gói.
cv2_datas, cv2_binaries, cv2_hidden = [], [], []
try:
    cv2_datas, cv2_binaries, cv2_hidden = collect_all("cv2")
except Exception:
    pass

a = Analysis(
    ["../run_ducktrap.py"],
    pathex=["."],
    binaries=cv2_binaries,
    datas=cv2_datas,
    hiddenimports=["PIL", "PIL.Image", "PIL.ImageTk"] + cv2_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DuckTrap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # windowed = không hiện cửa sổ console -> chạy âm thầm.
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# Trên macOS: bọc thành .app và khai báo lý do dùng Camera, nếu không macOS
# sẽ chặn camera âm thầm.
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="DuckTrap.app",
        icon=None,
        bundle_identifier="com.ducktrap.app",
        info_plist={
            "NSCameraUsageDescription":
                "Duck Trap chụp ảnh khi có người chạm vào máy đang khoá bẫy.",
            "LSUIElement": True,  # không hiện icon trên Dock
            "CFBundleName": "DuckTrap",
            "CFBundleDisplayName": "Duck Trap",
        },
    )
