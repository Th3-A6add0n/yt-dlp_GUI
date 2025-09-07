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
from urllib.parse import urljoin

# Detect the platform
system = platform.system().lower()
# Also detect the architecture
architecture = platform.machine().lower()

# Map system name to folder name
if system == 'darwin':
    platform_folder = 'macos'  # Map 'darwin' to 'macos' folder
else:
    platform_folder = system

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
    # Detect the architecture
    architecture = platform.machine().lower()
    
    # Set URLs based on architecture
    if architecture == 'arm64':
        # For arm64 macOS, use the universal binary from yt-dlp
        YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
        
        # For arm64 macOS, we'll determine the URL dynamically
        FFMPEG_URL = None  # Will be determined dynamically
        FFPROBE_URL = None  # Will be determined dynamically
    else:  # x86_64
        # For Intel macOS, use the universal binary from yt-dlp
        YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
        
        # For Intel macOS, we'll determine the URL dynamically
        FFMPEG_URL = None  # Will be determined dynamically
        FFPROBE_URL = None  # Will be determined dynamically
    
    FFMPEG_BINARIES = ["ffmpeg", "ffprobe"]
else:
    print(f"Unsupported platform: {system}")
    sys.exit(1)

# Define the assets directory
ASSETS_DIR = Path(__file__).parent / "assets" / platform_folder

# Define the root assets directory (for the icon)
ROOT_ASSETS_DIR = Path(__file__).parent / "assets"

def get_martin_riedl_urls(arch):
    """Get the download URLs for Martin Riedl's ffmpeg builds."""
    base_url = "https://ffmpeg.martin-riedl.de/"
    
    try:
        # Get the download page
        response = requests.get(base_url)
        response.raise_for_status()
        
        # Parse the HTML to find the download links
        import re
        from html.parser import HTMLParser
        
        class LinkParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    attrs_dict = dict(attrs)
                    if 'href' in attrs_dict:
                        href = attrs_dict['href']
                        # Only include direct download links, not checksum files
                        if href.endswith('.zip') and not href.endswith('.zip.sha256'):
                            self.links.append(href)
        
        parser = LinkParser()
        parser.feed(response.text)
        
        # Find the links for the specified architecture
        arch_pattern = f"download/macos/{arch}/"
        ffmpeg_url = None
        ffprobe_url = None
        
        for link in parser.links:
            if arch_pattern in link and "ffmpeg.zip" in link:
                ffmpeg_url = urljoin(base_url, link)
            elif arch_pattern in link and "ffprobe.zip" in link:
                ffprobe_url = urljoin(base_url, link)
        
        return ffmpeg_url, ffprobe_url
    except Exception as e:
        print(f"Error getting Martin Riedl URLs: {e}")
        return None, None

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
        
        # For macOS ARM64, check if the binary is compatible before running
        if system == 'darwin' and architecture == 'arm64':
            # Check file format to ensure it's macOS ARM64
            try:
                file_check = subprocess.run(['file', str(executable_path)], 
                                          capture_output=True, text=True, check=True)
                if 'Mach-O 64-bit executable arm64' not in file_check.stdout:
                    print(f"Warning: ffmpeg binary is not macOS ARM64 compatible: {file_check.stdout}")
                    return "incompatible"
            except subprocess.CalledProcessError as e:
                print(f"Error checking file format: {e}")
                return "error"
        
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
        # For macOS ARM64, provide a more specific error message
        if system == 'darwin' and architecture == 'arm64' and "Exec format error" in str(e):
            print("This is likely due to an incompatible binary architecture. macOS ARM64 binaries are required for Apple Silicon Macs.")
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
        # If we hit a rate limit, assume we're up to date
        if "rate limit exceeded" in str(e).lower():
            print("Rate limit exceeded, assuming we're up to date")
            return "current"
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
        # If we hit a rate limit, assume we're up to date
        if "rate limit exceeded" in str(e).lower():
            print("Rate limit exceeded, assuming we're up to date")
            return "current"
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
        
        # If we hit rate limit, assume we're up to date
        if latest_version == "current":
            print(f"Rate limit exceeded, assuming yt-dlp is up to date (version {current_version})")
            return True
        
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
    if ffmpeg_path.exists() and (FFPROBE_URL is None or ffprobe_path.exists()):
        # Set executable permissions before trying to run them
        if not sys.platform.startswith('win'):
            ffmpeg_path.chmod(0o755)
            if FFPROBE_URL is not None:
                ffprobe_path.chmod(0o755)
        
        current_version = get_ffmpeg_version(ffmpeg_path)
        latest_version = get_latest_ffmpeg_version()
        
        # If we hit rate limit, assume we're up to date
        if latest_version == "current":
            print(f"Rate limit exceeded, assuming ffmpeg is up to date (version {current_version})")
            return True
        
        # For macOS ARM64, if the binary is incompatible, force redownload
        if system == 'darwin' and architecture == 'arm64' and current_version == "incompatible":
            print("Found incompatible ffmpeg binary. Redownloading...")
            # Remove the existing files
            if ffmpeg_path.exists():
                ffmpeg_path.unlink()
            if ffprobe_path.exists():
                ffprobe_path.unlink()
            # Continue with download
        elif current_version and latest_version and current_version == latest_version:
            print(f"ffmpeg and ffprobe are up to date (version {current_version})")
            return True
        else:
            print(f"Updating ffmpeg/ffprobe from {current_version} to {latest_version}")
    else:
        print("ffmpeg or ffprobe not found, downloading...")
    
    # Special handling for macOS
    if system == 'darwin':
        # Detect the architecture
        architecture = platform.machine().lower()
        
        # Get the URLs dynamically
        if architecture == 'arm64':
            ffmpeg_url, ffprobe_url = get_martin_riedl_urls('arm64')
        else:
            ffmpeg_url, ffprobe_url = get_martin_riedl_urls('amd64')
        
        if not ffmpeg_url:
            print("Error: Could not determine ffmpeg download URL")
            return False
        
        print(f"Using ffmpeg URL: {ffmpeg_url}")
        if ffprobe_url:
            print(f"Using ffprobe URL: {ffprobe_url}")
        
        # Download ffmpeg
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download ffmpeg
            ffmpeg_archive_path = temp_path / "ffmpeg.zip"
            if not download_file(ffmpeg_url, ffmpeg_archive_path):
                return False
            
            # Verify it's a valid ZIP file
            try:
                with zipfile.ZipFile(ffmpeg_archive_path, 'r') as test_zip:
                    test_zip.testzip()
            except zipfile.BadZipFile:
                print("Error: Downloaded file is not a valid ZIP file")
                return False
            
            # Extract ffmpeg
            try:
                with zipfile.ZipFile(ffmpeg_archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the ffmpeg binary
                ffmpeg_found = False
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == "ffmpeg" and not ffmpeg_found:
                            source_path = os.path.join(root, file)
                            shutil.copy2(source_path, ffmpeg_path)
                            ffmpeg_path.chmod(0o755)
                            ffmpeg_found = True
                            print(f"Copied ffmpeg to {ffmpeg_path}")
                
                if not ffmpeg_found:
                    print("Error: Could not find ffmpeg in the archive.")
                    return False
                
                # Verify the binary is macOS compatible
                try:
                    ffmpeg_check = subprocess.run(['file', str(ffmpeg_path)], 
                                                 capture_output=True, text=True, check=True)
                    
                    expected_format = 'Mach-O 64-bit executable arm64' if architecture == 'arm64' else 'Mach-O 64-bit executable x86_64'
                    if expected_format not in ffmpeg_check.stdout:
                        print(f"Warning: Downloaded ffmpeg binary is not compatible: {ffmpeg_check.stdout}")
                        return False
                        
                    print(f"Verified {architecture} compatibility for ffmpeg")
                except subprocess.CalledProcessError as e:
                    print(f"Error verifying binary compatibility: {e}")
                    return False
            except Exception as e:
                print(f"Error extracting ffmpeg: {e}")
                return False
        
        # Download ffprobe if URL is available
        if ffprobe_url:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Download ffprobe
                ffprobe_archive_path = temp_path / "ffprobe.zip"
                if not download_file(ffprobe_url, ffprobe_archive_path):
                    return False
                
                # Verify it's a valid ZIP file
                try:
                    with zipfile.ZipFile(ffprobe_archive_path, 'r') as test_zip:
                        test_zip.testzip()
                except zipfile.BadZipFile:
                    print("Error: Downloaded file is not a valid ZIP file")
                    return False
                
                # Extract ffprobe
                try:
                    with zipfile.ZipFile(ffprobe_archive_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Find the ffprobe binary
                    ffprobe_found = False
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file == "ffprobe" and not ffprobe_found:
                                source_path = os.path.join(root, file)
                                shutil.copy2(source_path, ffprobe_path)
                                ffprobe_path.chmod(0o755)
                                ffprobe_found = True
                                print(f"Copied ffprobe to {ffprobe_path}")
                
                    if not ffprobe_found:
                        print("Error: Could not find ffprobe in the archive.")
                        return False
                    
                    # Verify the binary is macOS compatible
                    try:
                        ffprobe_check = subprocess.run(['file', str(ffprobe_path)], 
                                                     capture_output=True, text=True, check=True)
                        
                        expected_format = 'Mach-O 64-bit executable arm64' if architecture == 'arm64' else 'Mach-O 64-bit executable x86_64'
                        if expected_format not in ffprobe_check.stdout:
                            print(f"Warning: Downloaded ffprobe binary is not compatible: {ffprobe_check.stdout}")
                            return False
                            
                        print(f"Verified {architecture} compatibility for ffprobe")
                    except subprocess.CalledProcessError as e:
                        print(f"Error verifying binary compatibility: {e}")
                        return False
                except Exception as e:
                    print(f"Error extracting ffprobe: {e}")
                    return False
        
        print("Downloaded ffmpeg and ffprobe")
        return True
    
    # For Windows and Linux (existing code)
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