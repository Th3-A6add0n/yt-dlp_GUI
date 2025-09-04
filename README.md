# yt-dlp GUI Downloader

A simple PyQt5-based GUI wrapper for yt-dlp that downloads the best video/audio quality and converts it to MP4 (H.264/AAC).

## Features
- Select output folder
- Choose quality (Best, Audio-only, 720p, 480p)
- Live log and progress bar
- Simple, single-file PyQt entrypoint

## Requirements
- Python 3.8+
- ffmpeg on PATH (required for merging/encoding) — download from https://ffmpeg.org (Windows: add the folder containing ffmpeg.exe to PATH)
- `yt-dlp` and `PyQt5` (see requirements.txt)

## Install
```bash
pip install -r requirements.txt
```

## Run (development)
```bash
python -m yt_dlp_gui.main
# or
python yt_dlp_gui/main.py
```

## Build standalone executable (Windows)
Install PyInstaller:
```bash
pip install pyinstaller
```

Create a single-file, windowed executable:
```bash
pyinstaller --onefile --windowed yt_dlp_gui/main.py -n yt-dlp-gui
```

Or use the provided spec:
```bash
pyinstaller yt_dlp_gui.spec
```

The resulting `.exe` will appear in `dist/`.

## Contributing
Pull requests welcome. Please follow standard GitHub flow:
1. Fork
2. Create a branch
3. Open a PR

## License
MIT
