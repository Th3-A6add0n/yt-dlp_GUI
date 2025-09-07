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
    icon_extension = '.icns'  # macOS uses .icns for icons
else:
    yt_dlp_name = 'yt-dlp'
    ffmpeg_name = 'ffmpeg'
    ffprobe_name = 'ffprobe'
    icon_extension = '.png'

# Define the icon path from the root assets folder
# For macOS, we need to check if icon.icns exists, if not, we'll use icon.png and convert it
if system == 'darwin':
    icon_icns_path = os.path.join(root_assets_dir, 'icon.icns')
    icon_png_path = os.path.join(root_assets_dir, 'icon.png')
    
    if os.path.exists(icon_icns_path):
        icon_path = icon_icns_path
    elif os.path.exists(icon_png_path):
        # We'll convert the PNG to ICNS during the build process
        icon_path = icon_png_path
        print(f"Note: Using icon.png, will convert to ICNS during build")
    else:
        print(f"Warning: No icon file found in {root_assets_dir}")
        icon_path = None
else:
    # For Windows and Linux, use the appropriate icon extension
    icon_path = os.path.join(root_assets_dir, f'icon{icon_extension}')

# Check if icon file exists
if icon_path and not os.path.exists(icon_path):
    print(f"Warning: Icon file {icon_path} not found. Building without icon.")
    icon_path = None

block_cipher = None

a = Analysis(
    ['yt_dlp_gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include the binaries in the correct folder structure
        (os.path.join(assets_dir, yt_dlp_name), os.path.join('assets', platform_folder)),
        (os.path.join(assets_dir, ffmpeg_name), os.path.join('assets', platform_folder)),
        (os.path.join(assets_dir, ffprobe_name), os.path.join('assets', platform_folder)),
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
    # Include platform plugins
    platforms_path = os.path.join(qt_plugins_path, 'platforms')
    if os.path.exists(platforms_path):
        a.datas += Tree(
            platforms_path,
            prefix='platforms',
            excludes=[]
        )
    
    # Include image formats
    image_formats_path = os.path.join(qt_plugins_path, 'imageformats')
    if os.path.exists(image_formats_path):
        a.datas += Tree(
            image_formats_path,
            prefix='imageformats',
            excludes=[]
        )
    
    # For macOS and Linux, include xcbglintegrations
    if system in ['darwin', 'linux']:
        xcbglintegrations_path = os.path.join(qt_plugins_path, 'xcbglintegrations')
        if os.path.exists(xcbglintegrations_path):
            a.datas += Tree(
                xcbglintegrations_path,
                prefix='xcbglintegrations',
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

# For macOS, if we used a PNG icon, we need to convert it to ICNS
if system == 'darwin' and icon_path and icon_path.endswith('.png'):
    import subprocess
    import tempfile
    
    try:
        # Create a temporary directory for conversion
        with tempfile.TemporaryDirectory() as temp_dir:
            iconset_dir = os.path.join(temp_dir, 'icon.iconset')
            os.makedirs(iconset_dir)
            
            # Convert PNG to different sizes for the iconset
            sizes = [
                (16, 'icon_16x16.png'),
                (32, 'icon_16x16@2x.png'),
                (32, 'icon_32x32.png'),
                (64, 'icon_32x32@2x.png'),
                (128, 'icon_128x128.png'),
                (256, 'icon_128x128@2x.png'),
                (256, 'icon_256x256.png'),
                (512, 'icon_256x256@2x.png'),
                (512, 'icon_512x512.png'),
                (1024, 'icon_512x512@2x.png')
            ]
            
            for size, filename in sizes:
                output_path = os.path.join(iconset_dir, filename)
                subprocess.run(['sips', '-z', str(size), str(size), icon_path, '--out', output_path], 
                              check=True, capture_output=True)
            
            # Convert iconset to ICNS
            icns_path = os.path.join(root_assets_dir, 'icon.icns')
            subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path], 
                          check=True, capture_output=True)
            
            print(f"Successfully converted PNG to ICNS: {icns_path}")
    except Exception as e:
        print(f"Warning: Failed to convert PNG to ICNS: {e}")

# Clean up build directories
build_dir = os.path.join(current_dir, 'build')
if os.path.exists(build_dir):
    import shutil
    shutil.rmtree(build_dir)