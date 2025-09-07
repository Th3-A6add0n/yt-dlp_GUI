import os
import sys
import requests
import zipfile
import tempfile
import shutil
import subprocess
import re
from pathlib import Path

# Define URLs for the binaries
YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

# Define the assets directory - this needs to be fixed
ASSETS_DIR = Path("yt_dlp_gui/assets")

def get_yt_dlp_version(executable_path):
    """Get the version of the installed yt-dlp executable."""
    try:
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
        result = subprocess.run([str(executable_path), "-version"], 
                              capture_output=True, text=True, check=True)
        first_line = result.stdout.split('\n')[0]
        print(f"FFmpeg version output: {first_line}")
        
        # Try multiple patterns to extract version
        patterns = [
            r'ffmpeg version (\d+\.\d+(?:\.\d+)?)',  # Standard version pattern
            r'ffmpeg version n(\d+\.\d+(?:\.\d+)?)',  # Sometimes there's an 'n' prefix
            r'version (\d+\.\d+(?:\.\d+)?)',         # Just the version part
            r'N-(\d+)-g',                         # For nightly builds like "N-121001-gadc66f30ee"
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
            r'ffmpeg-(\d+\.\d+(?:\.\d+)?)',  # Standard pattern
            r'-(\d+\.\d+(?:\.\d+)?)'          # Just the version part after a dash
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
        response = requests.get(url, stream=True)
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
    """Download the latest yt-dlp.exe if needed."""
    destination = ASSETS_DIR / "yt-dlp.exe"
    
    # Check if file exists
    if destination.exists():
        current_version = get_yt_dlp_version(destination)
        latest_version = get_latest_yt_dlp_version()
        
        if current_version and latest_version and current_version == latest_version:
            print(f"yt-dlp.exe is up to date (version {current_version})")
            return True
        else:
            print(f"Updating yt-dlp.exe from {current_version} to {latest_version}")
    else:
        print("yt-dlp.exe not found, downloading...")
    
    return download_file(YT_DLP_URL, destination)

def download_ffmpeg():
    """Download and extract ffmpeg.exe and ffprobe.exe if needed."""
    ffmpeg_path = ASSETS_DIR / "ffmpeg.exe"
    ffprobe_path = ASSETS_DIR / "ffprobe.exe"
    
    # Check if both files exist
    if ffmpeg_path.exists() and ffprobe_path.exists():
        current_version = get_ffmpeg_version(ffmpeg_path)
        latest_version = get_latest_ffmpeg_version()
        
        print(f"Current ffmpeg version: {current_version}")
        print(f"Latest ffmpeg version: {latest_version}")
        
        # For FFmpeg-Builds, we'll always download the latest since version comparison is tricky
        # with nightly builds and "latest" tags
        if current_version and latest_version and current_version == latest_version:
            print(f"ffmpeg.exe and ffprobe.exe are up to date (version {current_version})")
            return True
        else:
            print(f"Updating ffmpeg/ffprobe from {current_version} to {latest_version}")
    else:
        print("ffmpeg.exe or ffprobe.exe not found, downloading...")
    
    # Create a temporary directory for the zip file
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "ffmpeg.zip"
        
        # Download the zip file
        if not download_file(FFMPEG_URL, zip_path):
            return False
        
        # Extract the zip file
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(temp_dir)
                
                # Find the bin directory
                bin_dir = None
                for root, dirs, files in os.walk(temp_dir):
                    if "bin" in dirs:
                        bin_dir = os.path.join(root, "bin")
                        break
                
                if not bin_dir:
                    print("Error: Could not find bin directory in the ffmpeg zip file.")
                    return False
                
                # Copy ffmpeg.exe and ffprobe.exe to the assets directory
                shutil.copy2(os.path.join(bin_dir, "ffmpeg.exe"), ASSETS_DIR)
                shutil.copy2(os.path.join(bin_dir, "ffprobe.exe"), ASSETS_DIR)
                
                print("Downloaded and extracted ffmpeg.exe and ffprobe.exe")
                return True
        except Exception as e:
            print(f"Error extracting ffmpeg: {e}")
            return False

def main():
    """Main function to download all required binaries."""
    try:
        # Create the assets directory if it doesn't exist
        ASSETS_DIR.mkdir(exist_ok=True)
        
        # Download yt-dlp
        if not download_yt_dlp():
            print("Failed to download yt-dlp.exe")
            return False
        
        # Download ffmpeg and ffprobe
        if not download_ffmpeg():
            print("Failed to download ffmpeg.exe and/or ffprobe.exe")
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