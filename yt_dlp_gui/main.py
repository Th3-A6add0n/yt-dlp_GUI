import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QLabel, QTextEdit, QProgressBar, QFileDialog, QComboBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import qdarktheme

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, url, output_dir, quality):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.quality = quality

    def run(self):
        command = [
            "yt-dlp",
            "-o", os.path.join(self.output_dir, "%(title)s.%(ext)s")
        ]

        if self.quality == "Best":
            format_str = "bestvideo+bestaudio/best"
            command += ["-f", format_str, "--merge-output-format", "mp4", "--recode-video", "mp4", "--postprocessor-args", "-c:v libx264 -c:a aac"]
        elif self.quality == "4K (2160p)":
            format_str = "bestvideo[height<=2160]+bestaudio/best"
            command += ["-f", format_str]
        elif self.quality == "2K (1440p)":
            format_str = "bestvideo[height<=1440]+bestaudio/best"
            command += ["-f", format_str]
        elif self.quality == "1080p":
            format_str = "bestvideo[height<=1080]+bestaudio/best"
            command += ["-f", format_str]
        elif self.quality == "720p":
            format_str = "bestvideo[height<=720]+bestaudio/best"
            command += ["-f", format_str]
        elif self.quality == "480p":
            format_str = "bestvideo[height<=480]+bestaudio/best"
            command += ["-f", format_str]
        elif self.quality == "360p":
            format_str = "bestvideo[height<=360]+bestaudio/best"
            command += ["-f", format_str]
        elif self.quality == "Audio (MP3)":
            command += ["-f", "bestaudio", "--extract-audio", "--audio-format", "mp3"]
        elif self.quality == "Audio (WAV)":
            command += ["-f", "bestaudio", "--extract-audio", "--audio-format", "wav"]
        elif self.quality == "Audio (M4A)":
            command += ["-f", "bestaudio", "--extract-audio", "--audio-format", "m4a"]

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=creation_flags)

        for line in process.stdout:
            self.log.emit(line.strip())
            if "%" in line:
                try:
                    percent = int(line.split("%")[0].split()[-1])
                    self.progress.emit(percent)
                except Exception:
                    pass

        process.wait()
        self.finished.emit()

class YtDlpApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp PyQt Downloader")
        self.setGeometry(200, 200, 700, 450)
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "assets", "icon.ico")
        self.setWindowIcon(QIcon("yt-dlp-gui/assets/icon.ico"))

        layout = QVBoxLayout()

        # URL Input
        self.url_label = QLabel("Enter URL (video/playlist):")
        self.url_entry = QLineEdit()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_entry)

        # Output folder selection
        self.folder_btn = QPushButton("Select Download Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        self.output_dir = os.getcwd()
        self.folder_label = QLabel(f"Download Folder: {self.output_dir}")
        layout.addWidget(self.folder_btn)
        layout.addWidget(self.folder_label)

        # Quality selection
        self.quality_label = QLabel("Select Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Best",
            "4K (2160p)",
            "2K (1440p)",
            "1080p",
            "720p",
            "480p",
            "360p",
            "Audio (MP3)",
            "Audio (WAV)",
            "Audio (M4A)"
        ])
        layout.addWidget(self.quality_label)
        layout.addWidget(self.quality_combo)

        # Download button
        self.download_btn = QPushButton("Download & Convert")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", os.getcwd())
        if folder:
            self.output_dir = folder
            self.folder_label.setText(f"Download Folder: {self.output_dir}")

    def start_download(self):
        url = self.url_entry.text().strip()
        quality = self.quality_combo.currentText()

        if not url:
            self.log_output.append("[ERROR] Please enter a URL.")
            return

        self.download_thread = DownloadThread(url, self.output_dir, quality)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.log.connect(self.log_output.append)
        self.download_thread.finished.connect(lambda: self.log_output.append("[DONE] Download complete!"))
        self.download_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    window = YtDlpApp()
    window.show()
    sys.exit(app.exec_())
