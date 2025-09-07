import os
import sys
import subprocess
import shutil
import platform
import plistlib
import signal
import stat
import tarfile
import tempfile
from pathlib import Path

def run_command(cmd, check=True, cwd=None, timeout=None):
    """Run a command and optionally check its return code."""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    # Set a longer timeout for PyInstaller
    if timeout is None and len(cmd) > 0 and "pyinstaller" in cmd[0].lower():
        timeout = 3600  # 1 hour timeout for PyInstaller
    
    try:
        # Set up signal handlers to prevent keyboard interrupt
        def signal_handler(sig, frame):
            print(f"Received signal {sig}, ignoring...")
            # Don't exit, just continue
        
        # Register signal handlers for SIGINT (Ctrl+C) and SIGTERM
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        result = subprocess.run(cmd, check=False, text=True, capture_output=True, cwd=cwd, timeout=timeout)
        
        # Restore original signal handlers
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        # Restore original signal handlers
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
        if check:
            raise
        return None

def create_macos_app_bundle(dist_dir, app_name):
    """Create a macOS application bundle."""
    print("Creating macOS application bundle...")
    
    # Create the .app directory structure
    app_bundle = dist_dir / f"{app_name}.app"
    contents_dir = app_bundle / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Create directories
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    # Move the executable to the MacOS directory
    executable_path = dist_dir / app_name
    if executable_path.exists():
        shutil.move(str(executable_path), str(macos_dir / app_name))
        print(f"Moved executable to {macos_dir / app_name}")
    else:
        print(f"Error: Executable not found at {executable_path}")
        return False
    
    # Create Info.plist
    info_plist = {
        'CFBundleExecutable': app_name,
        'CFBundleIdentifier': 'com.yt-dlp-gui.app',
        'CFBundleName': app_name,
        'CFBundleDisplayName': 'yt-dlp GUI',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '10.12.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDocumentTypes': [],
        'UTExportedTypeDeclarations': []
    }
    
    with open(contents_dir / "Info.plist", 'wb') as f:
        plistlib.dump(info_plist, f)
    
    print(f"Created Info.plist at {contents_dir / 'Info.plist'}")
    
    # Copy the icon if it exists
    icon_source = Path(__file__).parent / "yt_dlp_gui" / "assets" / "macos" / "icon.icns"
    if not icon_source.exists():
        # Try the root assets directory
        icon_source = Path(__file__).parent / "yt_dlp_gui" / "assets" / "icon.icns"
    
    if icon_source.exists():
        shutil.copy(str(icon_source), str(resources_dir / "icon.icns"))
        print(f"Copied icon to {resources_dir / 'icon.icns'}")
        
        # Update Info.plist to include the icon
        info_plist['CFBundleIconFile'] = 'icon.icns'
        with open(contents_dir / "Info.plist", 'wb') as f:
            plistlib.dump(info_plist, f)
        print("Updated Info.plist with icon reference")
    
    # Create a plugins directory in Resources
    plugins_dir = resources_dir / "plugins"
    plugins_dir.mkdir(exist_ok=True)
    
    # Copy Qt plugins if they exist
    qt_plugins_source = dist_dir / "platforms"
    if qt_plugins_source.exists():
        platforms_target = plugins_dir / "platforms"
        platforms_target.mkdir(exist_ok=True)
        for plugin in qt_plugins_source.glob("*"):
            if plugin.is_file():
                shutil.copy(str(plugin), str(platforms_target))
        print(f"Copied Qt platform plugins to {platforms_target}")
    
    # Copy other Qt plugins if they exist
    for plugin_dir in ["imageformats", "xcbglintegrations"]:
        plugin_source = dist_dir / plugin_dir
        if plugin_source.exists():
            plugin_target = plugins_dir / plugin_dir
            plugin_target.mkdir(exist_ok=True)
            for plugin in plugin_source.glob("*"):
                if plugin.is_file():
                    shutil.copy(str(plugin), str(plugin_target))
            print(f"Copied Qt {plugin_dir} plugins to {plugin_target}")
    
    # Create a wrapper script to set environment variables
    wrapper_script = macos_dir / f"{app_name}_wrapper.sh"
    with open(wrapper_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('# Set the path to the bundle\n')
        f.write('BUNDLE_DIR="$(dirname "$0")"\n')
        f.write('BUNDLE="$(dirname "$BUNDLE_DIR")"\n')
        f.write('RESOURCES="$BUNDLE/Resources"\n\n')
        f.write('# Set Qt plugin path\n')
        f.write('export QT_PLUGIN_PATH="$RESOURCES/plugins"\n')
        f.write('export QT_QPA_PLATFORM_PLUGIN_PATH="$RESOURCES/plugins/platforms"\n\n')
        f.write('# Run the actual executable\n')
        f.write('exec "$BUNDLE_DIR/{}" "$@"\n'.format(app_name))
    
    # Make the wrapper script executable
    wrapper_script.chmod(0o755)
    
    # Rename the original executable and replace it with the wrapper
    original_executable = macos_dir / app_name
    backup_executable = macos_dir / f"{app_name}_bin"
    shutil.move(str(original_executable), str(backup_executable))
    shutil.move(str(wrapper_script), str(original_executable))
    
    print(f"Created wrapper script at {original_executable}")
    
    # Make the final executable executable
    original_executable.chmod(0o755)
    
    print(f"Successfully created macOS application bundle at {app_bundle}")
    return True

def create_macos_dmg(dist_dir, app_name):
    """Create a DMG file for the macOS application."""
    print("Creating macOS DMG...")
    
    app_bundle = dist_dir / f"{app_name}.app"
    dmg_path = dist_dir / f"{app_name}.dmg"
    temp_dmg_path = dist_dir / "temp.dmg"
    
    try:
        # Create a temporary DMG
        run_command([
            "hdiutil", "create", "-srcfolder", str(app_bundle), 
            "-volname", app_name, "-fs", "HFS+", 
            "-fsargs", "-c c=64,a=16,e=16", 
            "-format", "UDZO", str(temp_dmg_path)
        ])
        
        # Create the final DMG with better compression
        run_command([
            "hdiutil", "convert", str(temp_dmg_path), 
            "-format", "UDZO", "-imagekey", "zlib-level=9", 
            "-o", str(dmg_path)
        ])
        
        # Clean up temporary files
        if temp_dmg_path.exists():
            temp_dmg_path.unlink()
        
        print(f"Successfully created DMG at {dmg_path}")
        return True
    except Exception as e:
        print(f"Error creating DMG: {e}")
        # Clean up temporary files
        if temp_dmg_path.exists():
            temp_dmg_path.unlink()
        return False

def create_linux_app_bundle(dist_dir, app_name):
    """Create a Linux application bundle."""
    print("Creating Linux application bundle...")
    
    # Create the app directory structure
    app_dir = dist_dir / f"{app_name}"
    bin_dir = app_dir / "bin"
    lib_dir = app_dir / "lib"
    plugins_dir = app_dir / "plugins"
    
    # Check if the executable already exists as a file
    executable_path = dist_dir / app_name
    if executable_path.exists() and executable_path.is_file():
        # Move the executable to a temporary location
        temp_executable = dist_dir / f"{app_name}.bin"
        shutil.move(str(executable_path), str(temp_executable))
        print(f"Moved executable to temporary location: {temp_executable}")
    
    # Create directories
    bin_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)
    plugins_dir.mkdir(parents=True, exist_ok=True)
    
    # Move the executable to the bin directory
    if temp_executable.exists():
        shutil.move(str(temp_executable), str(bin_dir / app_name))
        print(f"Moved executable to {bin_dir / app_name}")
    else:
        print(f"Error: Executable not found")
        return False
    
    # Copy Qt plugins if they exist
    qt_plugins_source = dist_dir / "platforms"
    if qt_plugins_source.exists():
        platforms_target = plugins_dir / "platforms"
        platforms_target.mkdir(exist_ok=True)
        for plugin in qt_plugins_source.glob("*"):
            if plugin.is_file():
                shutil.copy(str(plugin), str(platforms_target))
        print(f"Copied Qt platform plugins to {platforms_target}")
    
    # Copy other Qt plugins if they exist
    for plugin_dir in ["imageformats", "xcbglintegrations"]:
        plugin_source = dist_dir / plugin_dir
        if plugin_source.exists():
            plugin_target = plugins_dir / plugin_dir
            plugin_target.mkdir(exist_ok=True)
            for plugin in plugin_source.glob("*"):
                if plugin.is_file():
                    shutil.copy(str(plugin), str(plugin_target))
            print(f"Copied Qt {plugin_dir} plugins to {plugin_target}")
    
    # Copy library dependencies
    # This is a simplified approach - in a real scenario, you might want to use ldd to find all dependencies
    # For now, we'll just copy any .so files in the dist directory
    for so_file in dist_dir.glob("*.so*"):
        if so_file.is_file():
            shutil.copy(str(so_file), str(lib_dir))
            print(f"Copied library {so_file.name} to {lib_dir}")
    
    # Create a desktop entry file
    desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={app_name}
Comment=Download videos from YouTube and other sites
Exec={app_dir}/bin/{app_name}
Icon={app_dir}/icon.png
Terminal=false
Categories=AudioVideo;Video;Network;
"""
    
    with open(app_dir / f"{app_name}.desktop", 'w') as f:
        f.write(desktop_entry)
    
    print(f"Created desktop entry at {app_dir / f'{app_name}.desktop'}")
    
    # Copy the icon if it exists
    icon_source = Path(__file__).parent / "yt_dlp_gui" / "assets" / "linux" / "icon.png"
    if not icon_source.exists():
        # Try the root assets directory
        icon_source = Path(__file__).parent / "yt_dlp_gui" / "assets" / "icon.png"
    
    if icon_source.exists():
        shutil.copy(str(icon_source), str(app_dir / "icon.png"))
        print(f"Copied icon to {app_dir / 'icon.png'}")
    
    # Create a launcher script
    launcher_script = app_dir / f"run_{app_name}.sh"
    with open(launcher_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write(f'# Set the app directory\n')
        f.write(f'APP_DIR="$(dirname "$0")"\n\n')
        f.write(f'# Set library path\n')
        f.write(f'export LD_LIBRARY_PATH="$APP_DIR/lib:$LD_LIBRARY_PATH"\n\n')
        f.write(f'# Set Qt plugin path\n')
        f.write(f'export QT_PLUGIN_PATH="$APP_DIR/plugins"\n')
        f.write(f'export QT_QPA_PLATFORM_PLUGIN_PATH="$APP_DIR/plugins/platforms"\n\n')
        f.write(f'# Run the application\n')
        f.write(f'exec "$APP_DIR/bin/{app_name}" "$@"\n')
    
    # Make the launcher script executable
    launcher_script.chmod(0o755)
    
    # Make the main executable executable
    (bin_dir / app_name).chmod(0o755)
    
    print(f"Successfully created Linux application bundle at {app_dir}")
    return True

def create_linux_appimage(dist_dir, app_name):
    """Create an AppImage for the Linux application."""
    print("Creating Linux AppImage...")
    
    app_dir = dist_dir / f"{app_name}"
    appimage_path = dist_dir / f"{app_name}.AppImage"
    appdir_path = dist_dir / f"{app_name}.AppDir"
    
    try:
        # Create the AppDir structure
        appdir_usr_bin = appdir_path / "usr" / "bin"
        appdir_usr_lib = appdir_path / "usr" / "lib"
        appdir_usr_share = appdir_path / "usr" / "share"
        appdir_usr_share_applications = appdir_usr_share / "applications"
        appdir_usr_share_icons = appdir_usr_share / "icons"
        appdir_usr_share_icons_hicolor = appdir_usr_share_icons / "hicolor"
        appdir_usr_share_icons_hicolor_256x256 = appdir_usr_share_icons_hicolor / "256x256"
        appdir_usr_share_icons_hicolor_256x256_apps = appdir_usr_share_icons_hicolor_256x256 / "apps"
        
        # Create directories
        appdir_usr_bin.mkdir(parents=True, exist_ok=True)
        appdir_usr_lib.mkdir(parents=True, exist_ok=True)
        appdir_usr_share_applications.mkdir(parents=True, exist_ok=True)
        appdir_usr_share_icons_hicolor_256x256_apps.mkdir(parents=True, exist_ok=True)
        
        # Copy the application files
        if app_dir.exists():
            # Copy executable
            app_executable = app_dir / "bin" / app_name
            if app_executable.exists():
                shutil.copy(str(app_executable), str(appdir_usr_bin / app_name))
                print(f"Copied executable to {appdir_usr_bin / app_name}")
            
            # Copy libraries
            app_lib = app_dir / "lib"
            if app_lib.exists():
                for lib_file in app_lib.glob("*"):
                    shutil.copy(str(lib_file), str(appdir_usr_lib))
                    print(f"Copied library {lib_file.name} to {appdir_usr_lib}")
            
            # Copy desktop file
            desktop_file = app_dir / f"{app_name}.desktop"
            if desktop_file.exists():
                shutil.copy(str(desktop_file), str(appdir_usr_share_applications))
                print(f"Copied desktop file to {appdir_usr_share_applications}")
            
            # Copy icon
            icon_file = app_dir / "icon.png"
            if icon_file.exists():
                shutil.copy(str(icon_file), str(appdir_usr_share_icons_hicolor_256x256_apps / f"{app_name}.png"))
                print(f"Copied icon to {appdir_usr_share_icons_hicolor_256x256_apps}")
        
        # Create the AppRun script
        apprun_path = appdir_path / "AppRun"
        with open(apprun_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('# Set the app directory\n')
            f.write('APPDIR="$(dirname "$(readlink -f "$0")")"\n\n')
            f.write('# Set library path\n')
            f.write('export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"\n\n')
            f.write('# Set Qt plugin path\n')
            f.write('export QT_PLUGIN_PATH="$APPDIR/usr/lib/plugins"\n')
            f.write('export QT_QPA_PLATFORM_PLUGIN_PATH="$APPDIR/usr/lib/plugins/platforms"\n\n')
            f.write('# Run the application\n')
            f.write('exec "$APPDIR/usr/bin/{}" "$@"\n'.format(app_name))
        
        # Make AppRun executable
        apprun_path.chmod(0o755)
        
        # Create the .desktop file for AppImage
        desktop_path = appdir_path / f"{app_name}.desktop"
        with open(desktop_path, 'w') as f:
            f.write(f"""[Desktop Entry]
Name={app_name}
Exec={app_name}
Icon={app_name}
Type=Application
Categories=AudioVideo;Video;Network;
Comment=Download videos from YouTube and other sites
Terminal=false
""")
        
        # Download appimagetool if not available
        appimagetool_url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        appimagetool_path = dist_dir / "appimagetool"
        
        if not appimagetool_path.exists():
            print("Downloading appimagetool...")
            run_command(["wget", "-O", str(appimagetool_path), appimagetool_url])
            appimagetool_path.chmod(0o755)
        
        # Create the AppImage
        run_command([
            str(appimagetool_path), 
            "--no-appstream",
            str(appdir_path), 
            str(appimage_path)
        ])
        
        # Clean up
        if appdir_path.exists():
            shutil.rmtree(appdir_path)
        
        print(f"Successfully created AppImage at {appimage_path}")
        return True
    except Exception as e:
        print(f"Error creating AppImage: {e}")
        # Clean up
        if appdir_path.exists():
            shutil.rmtree(appdir_path)
        return False

def build_application():
    """Build the application using PyInstaller."""
    print("Building the application...")
    
    # Get the directory of the build script
    script_dir = Path(__file__).parent.resolve()
    
    # Get the platform
    system = platform.system().lower()
    
    # Run fetch_binaries to download the required binaries
    print("Fetching binaries...")
    sys.path.insert(0, os.path.join(script_dir, 'yt_dlp_gui'))
    import fetch_binaries
    if not fetch_binaries.main():
        print("Failed to fetch binaries, but continuing with build...")
    
    # Look for the spec file in the root directory
    spec_file = script_dir / "yt_dlp_gui.spec"
    
    if spec_file.exists():
        print(f"Using spec file: {spec_file}")
        result = run_command(["pyinstaller", str(spec_file)], cwd=script_dir)
        if result is None:
            print("PyInstaller command timed out")
            return False
    else:
        print(f"Error: Spec file not found at {spec_file}")
        return False
    
    # Get the distribution directory
    dist_dir = script_dir / "dist"
    
    # For macOS, create an application bundle and DMG
    if system == 'darwin':
        app_name = "yt-dlp GUI"
        if not create_macos_app_bundle(dist_dir, app_name):
            print("Failed to create macOS application bundle")
            return False
        
        if not create_macos_dmg(dist_dir, app_name):
            print("Failed to create macOS DMG")
            return False
    
    # For Linux, create an application bundle and AppImage
    elif system == 'linux':
        app_name = "yt-dlp GUI"
        if not create_linux_app_bundle(dist_dir, app_name):
            print("Failed to create Linux application bundle")
            return False
        
        if not create_linux_appimage(dist_dir, app_name):
            print("Failed to create Linux AppImage")
            return False
    
    # For Windows, no special handling needed
    elif system == 'windows':
        executable_path = dist_dir / "yt-dlp GUI.exe"
        if executable_path.exists():
            print("Windows executable created successfully")
        else:
            print("Error: Windows executable not found")
            return False
    
    return True

def cleanup():
    """Clean up build files."""
    print("Cleaning up build files...")
    
    # Get the directory of the build script
    script_dir = Path(__file__).parent.resolve()
    
    # Clean up the build directory
    build_dir = script_dir / "build"
    if build_dir.exists():
        print(f"Deleting build directory: {build_dir}")
        shutil.rmtree(build_dir)
    
    # Clean up the assets directory in the root
    assets_dir = script_dir / "assets"
    if assets_dir.exists():
        print(f"Deleting assets directory: {assets_dir}")
        shutil.rmtree(assets_dir)
    
    # Clean up __pycache__ directories
    yt_dlp_gui_dir = script_dir / "yt_dlp_gui"
    pycache_dir = yt_dlp_gui_dir / "__pycache__"
    if pycache_dir.exists():
        print(f"Deleting __pycache__ directory: {pycache_dir}")
        shutil.rmtree(pycache_dir)
    
    # Only delete spec files that are not our main spec file
    for spec_file in script_dir.glob("*.spec"):
        if spec_file.name != "yt_dlp_gui.spec":
            print(f"Deleting spec file: {spec_file}")
            spec_file.unlink()

def main():
    """Main build function."""
    print("===========================================")
    print("   yt-dlp GUI Automated Build Script")
    print("===========================================")
    print()
    
    # Print current working directory and platform
    print(f"Current working directory: {Path.cwd()}")
    print(f"Platform: {platform.system()}")
    
    # Build application
    if not build_application():
        print("Failed to build application")
        return 1
    
    # Clean up
    cleanup()
    
    print()
    print("===========================================")
    print("   Build completed successfully!")
    print("   The application bundle is in the 'dist' folder.")
    print("===========================================")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())