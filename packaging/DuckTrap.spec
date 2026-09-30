# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Duck Trap (Windows and macOS).

Build:
    pip install pyinstaller
    pyinstaller packaging/DuckTrap.spec --noconfirm
Output: dist/DuckTrap.exe (Windows) or dist/DuckTrap.app (macOS).
"""

import sys

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all of opencv (cv2) so no binary is missing in the packaged build.
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
    # windowed = no console window -> runs silently.
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# macOS: wrap into a .app and declare the Camera usage reason, otherwise
# macOS silently blocks the camera.
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="DuckTrap.app",
        icon=None,
        bundle_identifier="com.ducktrap.app",
        info_plist={
            "NSCameraUsageDescription":
                "Duck Trap takes a photo when someone touches the trapped machine.",
            "LSUIElement": True,  # do not show a Dock icon
            "CFBundleName": "DuckTrap",
            "CFBundleDisplayName": "Duck Trap",
        },
    )
