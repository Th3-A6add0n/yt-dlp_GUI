# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import platform
from pathlib import Path

# Get the current directory where the spec file is located
current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# Get the platform
system = platform.system().lower()

# Define the assets directory based on platform
if system == 'darwin':
    platform_folder = 'macos'  # Map 'darwin' to 'macos' folder
else:
    platform_folder = system
assets_dir = os.path.join(current_dir, 'yt_dlp_gui', 'assets', platform_folder)

# Define the root assets directory (where the icon is located)
root_assets_dir = os.path.join(current_dir, 'yt_dlp_gui', 'assets')

# Define the binary names based on platform
if system == 'windows':
    yt_dlp_name = 'yt-dlp.exe'
    ffmpeg_name = 'ffmpeg.exe'
    ffprobe_name = 'ffprobe.exe'
    icon_extension = '.ico'
elif system == 'darwin':
    yt_dlp_name = 'yt-dlp_macos'
    ffmpeg_name = 'ffmpeg'
    ffprobe_name = 'ffprobe'
    icon_extension = '.png'
else:
    yt_dlp_name = 'yt-dlp'
    ffmpeg_name = 'ffmpeg'
    ffprobe_name = 'ffprobe'
    icon_extension = '.png'

# Define the icon path from the root assets folder
icon_path = os.path.join(root_assets_dir, f'icon{icon_extension}')

# Check if icon file exists
if not os.path.exists(icon_path):
    print(f"Warning: Icon file {icon_path} not found. Building without icon.")
    icon_path = None

block_cipher = None

a = Analysis(
    ['yt_dlp_gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(assets_dir, yt_dlp_name), 'assets'),
        (os.path.join(assets_dir, ffmpeg_name), 'assets'),
        (os.path.join(assets_dir, ffprobe_name), 'assets'),
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
    icon=icon_path,  # This will be None if icon doesn't exist
)

# Clean up build directories
build_dir = os.path.join(current_dir, 'build')
if os.path.exists(build_dir):
    import shutil
    shutil.rmtree(build_dir)