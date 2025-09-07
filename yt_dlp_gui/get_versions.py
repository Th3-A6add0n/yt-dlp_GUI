import os
import sys
import subprocess
import re
from pathlib import Path

# Paths to the binaries
assets_dir = Path("assets")
yt_dlp_path = assets_dir / "yt-dlp.exe"
ffmpeg_path = assets_dir / "ffmpeg.exe"

def get_version(command, args):
    try:
        result = subprocess.run([command] + args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "unknown"

# Get versions
yt_dlp_version = get_version(str(yt_dlp_path), ["--version"])
ffmpeg_version = get_version(str(ffmpeg_path), ["-version"])

# Extract the version string for ffmpeg (first line)
ffmpeg_version = ffmpeg_version.split('\n')[0]

# Output in a structured format
print(f"yt_dlp_version={yt_dlp_version}")
print(f"ffmpeg_version={ffmpeg_version}")