import sys
import os
from pathlib import Path
import contextlib
import io

# Define the assets directory relative to this script's location
ASSETS_DIR = Path(__file__).parent / "assets"

# Import the functions from get_versions but suppress their debug output
with contextlib.redirect_stdout(io.StringIO()):
    from get_versions import get_yt_dlp_version, get_ffmpeg_version

def main():
    yt_dlp_exe = ASSETS_DIR / "yt-dlp.exe"
    ffmpeg_exe = ASSETS_DIR / "ffmpeg.exe"
    
    # Suppress debug output when calling these functions
    with contextlib.redirect_stdout(io.StringIO()):
        yt_dlp_version = get_yt_dlp_version(yt_dlp_exe) or ""
        ffmpeg_version = get_ffmpeg_version(ffmpeg_exe) or ""
    
    # Print only the key-value pairs for GitHub Actions
    print(f"yt_dlp_version={yt_dlp_version}")
    print(f"ffmpeg_version={ffmpeg_version}")

if __name__ == "__main__":
    main()