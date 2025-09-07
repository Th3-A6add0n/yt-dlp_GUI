import os
import sys
import subprocess
import shutil
import requests
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

def check_python():
    """Check if Python is installed and install it if needed."""
    try:
        result = run_command([sys.executable, "--version"], check=False)
        if result.returncode == 0:
            print(f"Python is already installed: {result.stdout.strip()}")
            return sys.executable
    except Exception as e:
        print(f"Error checking Python: {e}")
    
    print("Python is not installed. Downloading Python installer...")
    python_version = "3.11.4"
    installer_name = f"python-{python_version}-amd64.exe"
    installer_url = f"https://www.python.org/ftp/python/{python_version}/{installer_name}"
    
    # Download the installer
    print(f"Downloading {installer_url}...")
    response = requests.get(installer_url, stream=True)
    with open(installer_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Install Python
    print("Installing Python...")
    run_command([installer_name, "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0"])
    
    # Clean up
    os.remove(installer_name)
    
    # Find the installed Python
    python_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Programs" / "Python" / f"Python{python_version.replace('.', '')}"
    python_exe = python_path / "python.exe"
    
    if python_exe.exists():
        print(f"Python installed at: {python_exe}")
        return str(python_exe)
    else:
        print("Could not find installed Python")
        return None

def install_packages(python_exe):
    """Install required Python packages."""
    print("Installing required packages...")
    pip_exe = str(Path(python_exe).parent / "Scripts" / "pip.exe")
    
    run_command([pip_exe, "install", "--upgrade", "pip"])
    run_command([pip_exe, "install", "PyQt5", "PyInstaller", "requests"])

def download_binaries(python_exe):
    """Download required binaries."""
    print("Downloading required binaries...")
    
    # Get the directory of the build script
    script_dir = Path(__file__).parent.resolve()
    print(f"Script directory: {script_dir}")
    
    # Look for fetch_binaries.py in the yt_dlp_gui subdirectory
    yt_dlp_gui_dir = script_dir / "yt_dlp_gui"
    print(f"Checking yt_dlp_gui subdirectory: {yt_dlp_gui_dir}")
    
    if yt_dlp_gui_dir.exists():
        print("Files in yt_dlp_gui subdirectory:")
        for item in yt_dlp_gui_dir.iterdir():
            print(f"  {item.name}")
        
        fetch_binaries_path = yt_dlp_gui_dir / "fetch_binaries.py"
        print(f"Looking for fetch_binaries.py at: {fetch_binaries_path}")
        
        if not fetch_binaries_path.exists():
            print(f"Error: fetch_binaries.py not found at {fetch_binaries_path}")
            return False
    else:
        print(f"Error: yt_dlp_gui subdirectory not found at {yt_dlp_gui_dir}")
        return False
    
    # Run the fetch_binaries.py script with detailed output
    try:
        run_command([python_exe, "-u", str(fetch_binaries_path)], cwd=yt_dlp_gui_dir)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading binaries: {e}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    return True

def build_application():
    """Build the application using PyInstaller."""
    print("Building the application...")
    
    # Get the directory of the build script
    script_dir = Path(__file__).parent.resolve()
    
    # Look for the spec file in the root directory
    spec_file = script_dir / "yt_dlp_gui.spec"
    
    if spec_file.exists():
        print(f"Using spec file: {spec_file}")
        run_command(["pyinstaller", str(spec_file)], cwd=script_dir)
    else:
        print(f"Error: Spec file not found at {spec_file}")
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
    
    # Print current working directory
    print(f"Current working directory: {Path.cwd()}")
    
    # Check/install Python
    python_exe = check_python()
    if not python_exe:
        print("Failed to install Python")
        return 1
    
    # Install packages
    install_packages(python_exe)
    
    # Create assets directory if it doesn't exist
    assets_dir = Path("assets")
    if not assets_dir.exists():
        assets_dir.mkdir()
    
    # Download binaries
    if not download_binaries(python_exe):
        print("Failed to download binaries")
        return 1
    
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