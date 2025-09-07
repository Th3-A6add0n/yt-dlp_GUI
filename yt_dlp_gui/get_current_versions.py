import sys
import os
import subprocess
import re
from pathlib import Path

# Define the assets directory relative to this script's location
ASSETS_DIR = Path(__file__).parent / "assets"

# Detect the platform
system = sys.platform.lower()

if system.startswith('win'):
    platform_dir = 'windows'
    yt_dlp_name = 'yt-dlp.exe'
    ffmpeg_name = 'ffmpeg.exe'
    ffprobe_name = 'ffprobe.exe'
elif system.startswith('linux'):
    platform_dir = 'linux'
    yt_dlp_name = 'yt-dlp'
    ffmpeg_name = 'ffmpeg'
    ffprobe_name = 'ffprobe'
elif system.startswith('darwin'):
    platform_dir = 'macos'
    yt_dlp_name = 'yt-dlp'
    ffmpeg_name = 'ffmpeg'
    ffprobe_name = 'ffprobe'
else:
    print(f"Unsupported platform: {system}")
    print("yt_dlp_version=")
    print("ffmpeg_version=")
    sys.exit(0)

# Define the platform-specific assets directory
PLATFORM_DIR = ASSETS_DIR / platform_dir

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
        result = subprocess.run(
            [str(executable_path), "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        return version
    except Exception as e:
        print(f"Error getting yt-dlp version: {e}")
        return ""

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
        result = subprocess.run(
            [str(executable_path), "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        first_line = result.stdout.split('\n')[0]
        
        # Try to extract the publication date from the version string
        date_match = re.search(r'-(\d{8})\b', first_line)
        if date_match:
            date_str = date_match.group(1)
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
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
                return version
        
        # If all else fails, return the first line
        return first_line
    except Exception as e:
        print(f"Error getting ffmpeg version: {e}")
        return ""

def main():
    yt_dlp_path = PLATFORM_DIR / yt_dlp_name
    ffmpeg_path = PLATFORM_DIR / ffmpeg_name
    
    # Get versions
    yt_dlp_version = get_yt_dlp_version(yt_dlp_path)
    ffmpeg_version = get_ffmpeg_version(ffmpeg_path)
    
    # Print in GitHub Actions format
    print(f"yt_dlp_version={yt_dlp_version}")
    print(f"ffmpeg_version={ffmpeg_version}")

if __name__ == "__main__":
    main()