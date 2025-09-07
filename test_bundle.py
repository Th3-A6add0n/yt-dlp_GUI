import os
import sys
import subprocess
import platform

def test_bundle():
    """Test if the bundled application can start and find its dependencies."""
    system = platform.system().lower()
    
    if system == 'windows':
        exe_path = "dist/yt-dlp GUI_debug.exe"
    else:
        exe_path = "dist/yt-dlp GUI"
    
    if not os.path.exists(exe_path):
        print(f"Error: Executable not found at {exe_path}")
        return False
    
    print(f"Testing executable: {exe_path}")
    
    try:
        # Run the executable with a timeout
        result = subprocess.run(
            [exe_path, "--help"],
            timeout=10,
            capture_output=True,
            text=True
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("Test passed: Application started successfully")
            return True
        else:
            print("Test failed: Application returned non-zero exit code")
            return False
    except subprocess.TimeoutExpired:
        print("Test failed: Application timed out")
        return False
    except Exception as e:
        print(f"Test failed: Exception occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_bundle()
    sys.exit(0 if success else 1)