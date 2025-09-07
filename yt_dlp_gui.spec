# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import shutil
from pathlib import Path

# Get the current directory where the spec file is located
current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# Add the yt_dlp_gui directory to the path
sys.path.insert(0, os.path.join(current_dir, 'yt_dlp_gui'))

# Import and run the fetch_binaries script
import fetch_binaries
fetch_binaries.main()

block_cipher = None

# Get the absolute path to the assets directory
assets_dir = os.path.join(current_dir, 'yt_dlp_gui', 'assets')

a = Analysis(
    ['yt_dlp_gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(assets_dir, 'yt-dlp.exe'), 'assets'),
        (os.path.join(assets_dir, 'ffmpeg.exe'), 'assets'),
        (os.path.join(assets_dir, 'ffprobe.exe'), 'assets'),
        (os.path.join(assets_dir, 'icon.ico'), 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Include Qt platform plugins
import PyQt5
qt_plugins_path = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')

if os.path.exists(qt_plugins_path):
    a.datas += Tree(
        os.path.join(qt_plugins_path, 'platforms'),
        prefix='platforms',
        excludes=[]
    )
    a.datas += Tree(
        os.path.join(qt_plugins_path, 'imageformats'),
        prefix='imageformats',
        excludes=[]
    )

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='yt-dlp GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(assets_dir, 'icon.ico'),
)

# Clean up build directories
build_dir = os.path.join(current_dir, 'build')
if os.path.exists(build_dir):
    shutil.rmtree(build_dir)