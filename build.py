import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def run_command(cmd, check=True, cwd=None):
    """Run a command and optionally check its return code."""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    result = subprocess.run(cmd, check=False, text=True, capture_output=True, cwd=cwd)
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
    fetch_binaries.main()
    
    # Look for the spec file in the root directory
    spec_file = script_dir / "yt_dlp_gui.spec"
    
    if spec_file.exists():
        print(f"Using spec file: {spec_file}")
        run_command(["pyinstaller", str(spec_file)], cwd=script_dir)
    else:
        print(f"Error: Spec file not found at {spec_file}")
        return False
    
    # Rename the executable for non-Windows platforms
    if system != 'windows':
        dist_dir = script_dir / "dist"
        executable_path = dist_dir / "yt-dlp GUI"
        if executable_path.exists():
            print(f"Setting executable permission for {system}")
            os.chmod(executable_path, 0o755)
    
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
    print("   The executable is in the 'dist' folder.")
    print("===========================================")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())