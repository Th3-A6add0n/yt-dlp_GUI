import os
import sys
import platform
import requests
import zipfile
import tarfile
import tempfile
import shutil
import subprocess
import re
from pathlib import Path

# Detect the platform
system = platform.system().lower()
# Also detect the architecture
architecture = platform.machine().lower()

# Define URLs and file names based on platform
if system == 'windows':
    YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    FFMPEG_BINARIES = ["ffmpeg.exe", "ffprobe.exe"]
elif system == 'linux':
    YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    FFMPEG_BINARIES = ["ffmpeg", "ffprobe"]
elif system == 'darwin':  # macOS
    YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
    
    # Use different URLs based on architecture
    if architecture == 'arm64':
        # For ARM64 Macs, use Homebrew's precompiled binaries
        FFMPEG_URL = "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4.1/ffmpeg-darwin-arm64.tar.gz"
        FFPROBE_URL = "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4.1/ffprobe-darwin-arm64.tar.gz"
    else:
        # For Intel Macs, use the evermeet.cx URLs
        FFMPEG_URL = "https://evermeet.cx/ffmpeg/get/ffmpeg"
        FFPROBE_URL = "https://evermeet.cx/ffmpeg/get/ffprobe"
    
    FFMPEG_BINARIES = ["ffmpeg", "ffprobe"]
else:
    print(f"Unsupported platform: {system}")
    sys.exit(1)

# Define the assets directory
ASSETS_DIR = Path(__file__).parent / "assets" / system

# Define the root assets directory (for the icon)
ROOT_ASSETS_DIR = Path(__file__).parent / "assets"

def get_yt_dlp_version(executable_path):
    """Get the version of the installed yt-dlp executable."""
    try:
        # Make sure the file exists
        if not executable_path.exists():
            print(f"yt-dlp executable not found at {executable_path}")
            return ""
        
        # Make sure it's executable on non-Windows
        if not sys.platform.startswith('win'):
            executable_path.chmod(0o755)
        
        # Run the command
        result = subprocess.run([str(executable_path), "--version"], 
                              capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"Current yt-dlp version: {version}")
        return version
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting yt-dlp version: {e}")
        return None

def get_ffmpeg_version(executable_path):
    """Get the version of the installed ffmpeg executable."""
    try:
        # Make sure the file exists
        if not executable_path.exists():
            print(f"ffmpeg executable not found at {executable_path}")
            return ""
        
        # Make sure it's executable on non-Windows
        if not sys.platform.startswith('win'):
            executable_path.chmod(0o755)
        
        # Run the command
        result = subprocess.run([str(executable_path), "-version"], 
                              capture_output=True, text=True, check=True)
        first_line = result.stdout.split('\n')[0]
        print(f"FFmpeg version output: {first_line}")
        
        # Try to extract the publication date from the version string
        date_match = re.search(r'-(\d{8})\b', first_line)
        if date_match:
            date_str = date_match.group(1)
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            print(f"Extracted FFmpeg publication date: {formatted_date}")
            return formatted_date
        
        # If date extraction fails, try to extract build number
        patterns = [
            r'ffmpeg version N-(\d+)-g',
            r'ffmpeg version (\d+\.\d+(?:\.\d+)?)',
            r'ffmpeg version n(\d+\.\d+(?:\.\d+)?)',
            r'version (\d+\.\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, first_line)
            if match:
                version = match.group(1)
                print(f"Extracted FFmpeg version: {version}")
                return version
        
        print("Could not extract FFmpeg version from output")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e}")
        return None
    except FileNotFoundError:
        print(f"FFmpeg executable not found at {executable_path}")
        return None

def get_latest_yt_dlp_version():
    """Get the latest version of yt-dlp from GitHub API."""
    try:
        response = requests.get("https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest")
        response.raise_for_status()
        data = response.json()
        version = data["tag_name"]
        print(f"Latest yt-dlp version: {version}")
        return version
    except Exception as e:
        print(f"Error getting latest yt-dlp version: {e}")
        return None

def get_latest_ffmpeg_version():
    """Get the latest version of ffmpeg from GitHub API."""
    try:
        response = requests.get("https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest")
        response.raise_for_status()
        data = response.json()
        tag_name = data["tag_name"]
        print(f"Latest FFmpeg tag: {tag_name}")
        
        # For FFmpeg-Builds, the tag is often "latest" which doesn't contain version info
        # In this case, we'll use the commit date from the published_at field
        if tag_name == "latest":
            published_at = data.get("published_at", "")
            print(f"FFmpeg published at: {published_at}")
            # Use the date as a version string
            return published_at.split("T")[0] if published_at else "latest"
        
        # Try multiple patterns to extract version
        patterns = [
            r'ffmpeg-(\d+\.\d+(?:\.\d+)?)',
            r'-(\d+\.\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, tag_name)
            if match:
                version = match.group(1)
                print(f"Extracted latest FFmpeg version: {version}")
                return version
        
        print("Could not extract latest FFmpeg version from tag")
        return None
    except Exception as e:
        print(f"Error getting latest ffmpeg version: {e}")
        return None

def download_file(url, destination):
    """Download a file from a URL and save it to the destination."""
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, stream=True, timeout=60)  # Added timeout
        response.raise_for_status()
        
        # Write the file in chunks
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded {destination}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_yt_dlp():
    """Download the latest yt-dlp if needed."""
    destination = ASSETS_DIR / (YT_DLP_URL.split('/')[-1])
    
    # Check if file exists
    if destination.exists():
        # Set executable permission before trying to run it
        if not sys.platform.startswith('win'):
            destination.chmod(0o755)
        
        current_version = get_yt_dlp_version(destination)
        latest_version = get_latest_yt_dlp_version()
        
        if current_version and latest_version and current_version == latest_version:
            print(f"yt-dlp is up to date (version {current_version})")
            return True
        else:
            print(f"Updating yt-dlp from {current_version} to {latest_version}")
    else:
        print("yt-dlp not found, downloading...")
    
    return download_file(YT_DLP_URL, destination)

def download_ffmpeg():
    """Download and extract ffmpeg binaries if needed."""
    ffmpeg_path = ASSETS_DIR / FFMPEG_BINARIES[0]
    ffprobe_path = ASSETS_DIR / FFMPEG_BINARIES[1]
    
    # Check if both files exist
    if ffmpeg_path.exists() and ffprobe_path.exists():
        # Set executable permissions before trying to run them
        if not sys.platform.startswith('win'):
            ffmpeg_path.chmod(0o755)
            ffprobe_path.chmod(0o755)
        
        current_version = get_ffmpeg_version(ffmpeg_path)
        latest_version = get_latest_ffmpeg_version()
        
        if current_version and latest_version and current_version == latest_version:
            print(f"ffmpeg and ffprobe are up to date (version {current_version})")
            return True
        else:
            print(f"Updating ffmpeg/ffprobe from {current_version} to {latest_version}")
    else:
        print("ffmpeg or ffprobe not found, downloading...")
    
    # Special handling for macOS
    if system == 'darwin':
        # For macOS ARM64, download and extract tar.gz files
        if architecture == 'arm64':
            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Download ffmpeg
                ffmpeg_tar = temp_path / "ffmpeg.tar.gz"
                if not download_file(FFMPEG_URL, ffmpeg_tar):
                    return False
                
                # Download ffprobe
                ffprobe_tar = temp_path / "ffprobe.tar.gz"
                if not download_file(FFPROBE_URL, ffprobe_tar):
                    return False
                
                # Extract ffmpeg
                with tarfile.open(ffmpeg_tar, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                # Extract ffprobe
                with tarfile.open(ffprobe_tar, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                # Copy binaries to assets directory
                shutil.copy2(temp_path / "ffmpeg", ASSETS_DIR)
                shutil.copy2(temp_path / "ffprobe", ASSETS_DIR)
                
                # Set executable permissions
                (ASSETS_DIR / "ffmpeg").chmod(0o755)
                (ASSETS_DIR / "ffprobe").chmod(0o755)
                
                print("Downloaded and extracted ffmpeg and ffprobe")
                return True
        else:
            # For Intel Macs, download directly from evermeet.cx
            if not download_file(FFMPEG_URL, ffmpeg_path):
                return False
            
            if not download_file(FFPROBE_URL, ffprobe_path):
                return False
            
            # Set executable permissions
            ffmpeg_path.chmod(0o755)
            ffprobe_path.chmod(0o755)
            
            print("Downloaded ffmpeg and ffprobe")
            return True
    
    # For Windows and Linux
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Determine file extension based on platform
        if system == 'windows':
            archive_path = temp_path / "ffmpeg.zip"
            archive_format = 'zip'
        else:
            archive_path = temp_path / "ffmpeg.tar.xz"
            archive_format = 'tar'
        
        # Download the archive
        if not download_file(FFMPEG_URL, archive_path):
            return False
        
        # Extract the archive
        try:
            if archive_format == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            else:
                with tarfile.open(archive_path, 'r:xz') as tar_ref:
                    tar_ref.extractall(temp_dir)
            
            # Find the bin directory
            bin_dir = None
            for root, dirs, files in os.walk(temp_dir):
                if "bin" in dirs:
                    bin_dir = os.path.join(root, "bin")
                    break
            
            if not bin_dir:
                print("Error: Could not find bin directory in the ffmpeg archive.")
                return False
            
            # Copy ffmpeg and ffprobe to the assets directory
            for binary in FFMPEG_BINARIES:
                shutil.copy2(os.path.join(bin_dir, binary), ASSETS_DIR)
                # Set executable permission for non-Windows
                if system != 'windows':
                    os.chmod(ASSETS_DIR / binary, 0o755)
            
            print("Downloaded and extracted ffmpeg and ffprobe")
            return True
        except Exception as e:
            print(f"Error extracting ffmpeg: {e}")
            return False

def main():
    """Main function to download all required binaries."""
    try:
        # Create the root assets directory if it doesn't exist
        ROOT_ASSETS_DIR.mkdir(exist_ok=True, parents=True)
        
        # Create the platform-specific assets directory if it doesn't exist
        ASSETS_DIR.mkdir(exist_ok=True, parents=True)
        
        # Download yt-dlp
        if not download_yt_dlp():
            print("Failed to download yt-dlp")
            return False
        
        # Download ffmpeg and ffprobe
        if not download_ffmpeg():
            print("Failed to download ffmpeg and/or ffprobe")
            return False
        
        print("All binaries downloaded successfully!")
        return True
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)