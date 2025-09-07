



\# yt-dlp GUI



A simple and user-friendly GUI for yt-dlp, a command-line tool to download videos from YouTube and other sites.



!\[yt-dlp GUI Screenshot](https://i.ibb.co/wFT8sz8d/yt-dlp-GUI-813fx-O3-Wjh.png)



\## Features



\- Download videos from YouTube and other supported sites

\- Convert videos to various formats (MP4, MP3, WAV, M4A)

\- Select video quality (360p to 4K)

\- Dark and light theme support

\- Automatic updates for yt-dlp and FFmpeg binaries

\- User-friendly interface with progress tracking



\## For Users



\### Downloading the Application



You can download the latest release of yt-dlp GUI from the \[Releases page](https://github.com/yourusername/yt-dlp-gui/releases).



\### Installation



1\. Download the latest `yt-dlp GUI.exe` from the releases page.

2\. Place the executable anywhere on your computer.

3\. Run the executable - no installation required!



\### Usage



1\. Run `yt-dlp GUI.exe`

2\. Enter the video URL in the URL field

3\. Select the download folder by clicking "Browse..."

4\. Choose the desired quality from the dropdown menu

5\. Click "Download \& Convert"

6\. Monitor progress in the log area



\### Themes



The application supports both light and dark themes. Toggle between themes using the "Toggle Theme" button.



\## For Developers



\### Prerequisites



\- Python 3.11 or higher

\- Required Python packages (automatically installed by the build script)



\### Building from Source



\#### Method 1: Automated Build (Recommended)



The easiest way to build the application is using the automated build script:



1\. Clone the repository:

&nbsp;  ```bash

&nbsp;  git clone https://github.com/yourusername/yt-dlp-gui.git

&nbsp;  cd yt-dlp-gui

&nbsp;  ```



2\. Run the build script:

&nbsp;  ```bash

&nbsp;  python build.py

&nbsp;  ```



The build script will:

\- Check if Python is installed and install it if needed

\- Install required Python packages

\- Download the latest yt-dlp and FFmpeg binaries

\- Build the application using PyInstaller

\- Clean up temporary files



The built executable will be located in the `dist` folder.



\#### Method 2: Manual Build



If you prefer to build manually:



1\. Clone the repository:

&nbsp;  ```bash

&nbsp;  git clone https://github.com/yourusername/yt-dlp-gui.git

&nbsp;  cd yt-dlp-gui

&nbsp;  ```



2\. Install Python dependencies:

&nbsp;  ```bash

&nbsp;  pip install -r requirements.txt

&nbsp;  ```



3\. Download the required binaries:

&nbsp;  ```bash

&nbsp;  python yt\_dlp\_gui/fetch\_binaries.py

&nbsp;  ```



4\. Build the application:

&nbsp;  ```bash

&nbsp;  pyinstaller yt\_dlp\_gui.spec

&nbsp;  ```



5\. The built executable will be in the `dist` folder.



\### Project Structure



```

yt-dlp-gui/

├── .github/

│   └── workflows/

│       └── build-and-release.yml    # GitHub Actions workflow

├── assets/                         # Binary files (yt-dlp, ffmpeg, etc.)

├── dist/                           # Built executables

├── yt\_dlp\_gui/                     # Source code

│   ├── assets/                     # Local copy of binaries

│   ├── main.py                     # Main application code

│   ├── fetch\_binaries.py           # Script to download binaries

│   └── get\_versions.py             # Script to extract version info

├── build.py                        # Automated build script

├── yt\_dlp\_gui.spec                 # PyInstaller spec file

├── requirements.txt                # Python dependencies

└── README.md                       # This file

```



\### Automated Updates



This project uses GitHub Actions to automatically:



1\. Check for updates to yt-dlp and FFmpeg binaries every week

2\. Build the application with updated binaries

3\. Create a new release with the updated application



The workflow file is located at `.github/workflows/build-and-release.yml`.



\### Contributing



Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.



1\. Fork the repository

2\. Create your feature branch (`git checkout -b feature/amazing-feature`)

3\. Commit your changes (`git commit -m 'Add some amazing feature'`)

4\. Push to the branch (`git push origin feature/amazing-feature`)

5\. Open a Pull Request



\### Development Setup



1\. Clone the repository:

&nbsp;  ```bash

&nbsp;  git clone https://github.com/yourusername/yt-dlp-gui.git

&nbsp;  cd yt-dlp-gui

&nbsp;  ```



2\. Create a virtual environment:

&nbsp;  ```bash

&nbsp;  python -m venv venv

&nbsp;  source venv/bin/activate  # On Windows: venv\\Scripts\\activate

&nbsp;  ```



3\. Install dependencies:

&nbsp;  ```bash

&nbsp;  pip install -r requirements.txt

&nbsp;  ```



4\. Run the application in development mode:

&nbsp;  ```bash

&nbsp;  python yt\_dlp\_gui/main.py

&nbsp;  ```



\## License



This project is licensed under the MIT License - see the \[LICENSE](LICENSE) file for details.



\## Acknowledgments



\- \[yt-dlp](https://github.com/yt-dlp/yt-dlp) - A command-line tool to download videos from YouTube and other sites

\- \[FFmpeg](https://ffmpeg.org/) - A complete, cross-platform solution to record, convert and stream audio and video

\- \[PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - Python bindings for the Qt application framework

\- \[PyInstaller](https://pyinstaller.org/) - Converts Python programs into stand-alone executables



\## Support



If you encounter any issues or have questions, please open an issue on the \[GitHub Issues page](https://github.com/yourusername/yt-dlp-gui/issues).

