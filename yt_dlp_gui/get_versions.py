import subprocess
import os
from pathlib import Path

def get_version(command, args):
    try:
        result = subprocess.run([command] + args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "unknown"

# Paths to the binaries
assets_dir = Path("assets")
yt_dlp_path = assets_dir / "yt-dlp.exe"
ffmpeg_path = assets_dir / "ffmpeg.exe"

# Get versions
yt_dlp_version = get_version(str(yt_dlp_path), ["--version"])
ffmpeg_version = get_version(str(ffmpeg_path), ["-version"])

# Extract the version string for ffmpeg (first line)
ffmpeg_version = ffmpeg_version.split('\n')[0]

# Output to GitHub Actions step output
with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
    print(f"yt_dlp_version={yt_dlp_version}", file=fh)
    print(f"ffmpeg_version={ffmpeg_version}", file=fh)