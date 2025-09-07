import os
import sys
import json
import subprocess
import threading
import time
import re
import shutil
import platform
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QTextEdit, QFileDialog, QStyleFactory, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt5.QtGui import QIcon, QPalette, QColor

# Get the directory of the current script
if getattr(sys, 'frozen', False):
    # If running as a PyInstaller bundle
    APPLICATION_PATH = sys._MEIPASS
else:
    # If running as a script
    APPLICATION_PATH = os.path.dirname(os.path.abspath(__file__))

# Determine the platform
system = platform.system().lower()

# Path to the assets directory
ASSETS_DIR = os.path.join(APPLICATION_PATH, "assets", system)

# Path to the configuration file
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "yt_dlp_gui_config.json")

# Windows-specific flag to hide console windows
if sys.platform == "win32":
    CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
else:
    CREATE_NO_WINDOW = 0


class WorkerThread(QThread):
    """Worker thread for downloading and converting videos."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, output_dir, quality):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.quality = quality
        self.is_cancelled = False
        self.process = None
        self.process_convert = None

    def cancel(self):
        """Cancel the download and conversion process."""
        self.is_cancelled = True
        # Terminate the processes if they exist
        if self.process:
            self.process.terminate()
        if self.process_convert:
            self.process_convert.terminate()

    def process_file(self, file_path):
        """Process a single file (download or convert)."""
        if self.is_cancelled:
            self.log.emit("Processing cancelled.")
            return False

        self.log.emit(f"Processing file: {file_path}")
        file_ext = os.path.splitext(file_path)[1].lower()

        # Skip if it's already an audio file in the requested format
        if self.quality.startswith("Audio"):
            if (self.quality == "Audio (MP3)" and file_ext == ".mp3") or \
               (self.quality == "Audio (WAV)" and file_ext == ".wav") or \
               (self.quality == "Audio (M4A)" and file_ext == ".m4a"):
                self.progress.emit(100)  # Emit 100% if no conversion needed
                return True
        else:
            # For video, convert to MP4 with H.264 and AAC
            if file_ext == ".mp4":
                # Check if it's already H.264 + AAC
                cmd_check = [
                    os.path.join(ASSETS_DIR, "ffprobe.exe"),
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=codec_name",
                    "-of", "csv=p=0",
                    file_path
                ]
                try:
                    result = subprocess.run(
                        cmd_check, capture_output=True, text=True, check=True,
                        creationflags=CREATE_NO_WINDOW
                    )
                    video_codec = result.stdout.strip()

                    cmd_check = [
                        os.path.join(ASSETS_DIR, "ffprobe.exe"),
                        "-v", "error",
                        "-select_streams", "a:0",
                        "-show_entries", "stream=codec_name",
                        "-of", "csv=p=0",
                        file_path
                    ]
                    result = subprocess.run(
                        cmd_check, capture_output=True, text=True, check=True,
                        creationflags=CREATE_NO_WINDOW
                    )
                    audio_codec = result.stdout.strip()

                    if video_codec == "h264" and audio_codec == "aac":
                        self.progress.emit(100)  # Emit 100% if no conversion needed
                        return True
                except subprocess.CalledProcessError as e:
                    self.log.emit(f"Error checking codecs: {e}")
                    self.log.emit(f"Stderr: {e.stderr}")
                    # Continue with conversion

            # Get the output path
            output_path = os.path.splitext(file_path)[0] + ".mp4"

            # Get the duration of the video
            cmd_duration = [
                os.path.join(ASSETS_DIR, "ffprobe.exe"),
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                file_path
            ]
            try:
                self.log.emit(f"Getting duration for file: {file_path}")
                result = subprocess.run(
                    cmd_duration, capture_output=True, text=True, check=True,
                    creationflags=CREATE_NO_WINDOW
                )
                duration_str = result.stdout.strip()
                total_duration = float(duration_str)
            except subprocess.CalledProcessError as e:
                self.log.emit(f"Error getting duration: {e}")
                self.log.emit(f"Stderr: {e.stderr}")
                return False

            self.log.emit(f"Converting {file_path} to {output_path}")

            # Prepare the ffmpeg command
            cmd_convert = [
                os.path.join(ASSETS_DIR, "ffmpeg.exe"),
                "-i", file_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",  # Overwrite output file if it exists
                output_path
            ]

            # Run ffmpeg
            self.process_convert = subprocess.Popen(
                cmd_convert,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=CREATE_NO_WINDOW  # Prevents console window
            )

            # Parse output for progress
            for line in iter(self.process_convert.stdout.readline, ''):
                if self.is_cancelled:
                    self.process_convert.terminate()
                    self.log.emit("Conversion cancelled.")
                    return False

                self.log.emit(line.strip())

                # Extract time information
                match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    seconds = float(match.group(3))
                    current_time = hours * 3600 + minutes * 60 + seconds

                    if total_duration > 0:
                        percent = (current_time / total_duration) * 100
                        self.progress.emit(int(percent))

            # Wait for the process to complete
            return_code = self.process_convert.wait()
            if return_code != 0 and not self.is_cancelled:
                self.log.emit(f"ffmpeg exited with code {return_code}")
                return False

            self.progress.emit(100)  # Ensure progress bar reaches 100%

            # Delete the original file if it's different from the output file
            if file_path != output_path and os.path.exists(file_path):
                os.remove(file_path)
                self.log.emit(f"Deleted original file: {file_path}")

            return True

    def run(self):
        """Run the download and conversion process."""
        try:
            # Paths to the binaries
            yt_dlp_path = os.path.join(
                ASSETS_DIR,
                "yt-dlp.exe" if system == 'windows'
                else "yt-dlp_macos" if system == 'darwin'
                else "yt-dlp"
            )
            ffmpeg_path = os.path.join(ASSETS_DIR, "ffmpeg.exe" if system == 'windows' else "ffmpeg")
            ffprobe_path = os.path.join(ASSETS_DIR, "ffprobe.exe" if system == 'windows' else "ffprobe")

            # Check if the binaries exist
            if not os.path.exists(yt_dlp_path):
                self.log.emit(f"Error: {yt_dlp_path} not found.")
                self.finished.emit(False, "yt-dlp not found.")
                return

            if not os.path.exists(ffmpeg_path):
                self.log.emit(f"Error: {ffmpeg_path} not found.")
                self.finished.emit(False, "ffmpeg not found.")
                return

            if not os.path.exists(ffprobe_path):
                self.log.emit(f"Error: {ffprobe_path} not found.")
                self.finished.emit(False, "ffprobe not found.")
                return

            # Prepare the yt-dlp command
            cmd = [
                yt_dlp_path,
                "--no-warnings",
                "--ffmpeg-location", ffmpeg_path,
                "--output", os.path.join(self.output_dir, "%(title)s.%(ext)s"),
                "--no-keep-video"
            ]

            # Add format selection based on quality
            if self.quality == "Best":
                cmd.extend(["-f", "bestvideo+bestaudio/best"])
            elif self.quality == "4K (2160p)":
                cmd.extend(["-f", "bestvideo[height<=2160]+bestaudio/best[height<=2160]"])
            elif self.quality == "2K (1440p)":
                cmd.extend(["-f", "bestvideo[height<=1440]+bestaudio/best[height<=1440]"])
            elif self.quality == "1080p":
                cmd.extend(["-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"])
            elif self.quality == "720p":
                cmd.extend(["-f", "bestvideo[height<=720]+bestaudio/best[height<=720]"])
            elif self.quality == "480p":
                cmd.extend(["-f", "bestvideo[height<=480]+bestaudio/best[height<=480]"])
            elif self.quality == "360p":
                cmd.extend(["-f", "bestvideo[height<=360]+bestaudio/best[height<=360]"])
            elif self.quality == "Audio (MP3)":
                cmd.extend(["-x", "--audio-format", "mp3"])
            elif self.quality == "Audio (WAV)":
                cmd.extend(["-x", "--audio-format", "wav"])
            elif self.quality == "Audio (M4A)":
                cmd.extend(["-x", "--audio-format", "m4a"])

            # Add the URL
            cmd.append(self.url)

            self.log.emit(f"Running command: {' '.join(cmd)}")

            # Run yt-dlp
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=CREATE_NO_WINDOW
            )

            # Parse output for progress and file information
            final_file = None
            for line in iter(self.process.stdout.readline, ''):
                if self.is_cancelled:
                    self.process.terminate()
                    self.log.emit("Download cancelled.")
                    self.finished.emit(False, "Download cancelled.")
                    return

                self.log.emit(line.strip())

                # Extract filename if downloading
                if "[download] Destination:" in line:
                    current_file = line.split(":", 1)[1].strip()
                    self.log.emit(f"Downloading to: {current_file}")

                # Extract progress percentage
                match = re.search(r"\[download\]\s+(\d+\.\d+)%", line)
                if match:
                    percent = float(match.group(1))
                    self.progress.emit(int(percent))

                # Extract the final file path
                if "[Merger] Merging formats into" in line:
                    final_file = line.split("into", 1)[1].strip().strip('"')
                    self.log.emit(f"Merged file: {final_file}")

            # Wait for the process to complete
            return_code = self.process.wait()
            if return_code != 0 and not self.is_cancelled:
                self.log.emit(f"yt-dlp exited with code {return_code}")
                self.finished.emit(False, f"yt-dlp exited with code {return_code}")
                return

            # If we didn't find a merged file, look for any file in the output dir
            if not final_file:
                self.log.emit("No merged file found, looking for downloaded files...")
                output_files = [
                    os.path.join(self.output_dir, file)
                    for file in os.listdir(self.output_dir)
                    if os.path.isfile(os.path.join(self.output_dir, file))
                ]
                if output_files:
                    final_file = max(output_files, key=os.path.getmtime)
                    self.log.emit(f"Found file: {final_file}")
                else:
                    self.log.emit("Error: No files found in the output directory.")
                    self.finished.emit(False, "No files found in the output directory.")
                    return

            # Process the final file
            if final_file and os.path.exists(final_file):
                if not self.process_file(final_file):
                    self.finished.emit(False, "Error processing file.")
                    return
            else:
                self.log.emit(f"Error: File {final_file} not found.")
                self.finished.emit(False, "File not found after download.")
                return

            self.log.emit("Download and conversion completed successfully!")
            self.progress.emit(100)
            self.finished.emit(True, "Download and conversion completed successfully!")

        except Exception as e:
            self.log.emit(f"Error: {str(e)}")
            self.finished.emit(False, str(e))
