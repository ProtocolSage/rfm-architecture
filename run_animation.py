#!/usr/bin/env python
"""Run RFM animation with cross-platform compatibility."""
import os
import sys
import subprocess
import platform
import webbrowser

def check_python():
    """Check if Python is installed and has the required version."""
    try:
        python_version = subprocess.check_output(["python", "--version"]).decode().strip()
        print(f"Using {python_version}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            python_version = subprocess.check_output(["python3", "--version"]).decode().strip()
            print(f"Using {python_version}")
            # Set the alias to python3
            global PYTHON_CMD
            PYTHON_CMD = "python3"
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: Python is not installed or not in PATH!")
            print("Please install Python from https://www.python.org/downloads/")
            return False


def install_dependencies():
    """Install required packages."""
    packages = ["matplotlib", "numpy", "networkx", "pyyaml", "scipy", "pillow"]
    
    print("Installing required packages...")
    try:
        subprocess.check_call([PYTHON_CMD, "-m", "pip", "install"] + packages)
        return True
    except subprocess.SubprocessError as e:
        print(f"Error installing packages: {e}")
        return False


def run_animation(output_format="gif"):
    """Run the animation script with the specified format."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "animate_rfm.py")
    
    if not os.path.exists(script_path):
        print(f"Error: animate_rfm.py not found at {script_path}")
        return False
    
    output_file = "rfm_animation"
    dpi = 150
    fps = 30
    duration = 8
    
    print(f"Creating animation in {output_format.upper()} format...")
    try:
        subprocess.check_call([
            PYTHON_CMD, script_path,
            "--output", output_file,
            "--format", output_format,
            "--dpi", str(dpi),
            "--fps", str(fps),
            "--duration", str(duration)
        ])
        
        # Determine the full output path
        output_path = os.path.abspath(f"{output_file}.{output_format}")
        print(f"Animation saved to: {output_path}")
        
        return output_path
    except subprocess.SubprocessError as e:
        print(f"Error running animation script: {e}")
        return False


def open_animation(file_path):
    """Open the animation with the system's default application."""
    if not os.path.exists(file_path):
        print(f"Error: Animation file not found at {file_path}")
        return False
    
    print(f"Opening animation: {file_path}")
    
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", file_path])
        else:  # Linux and others
            subprocess.call(["xdg-open", file_path])
        return True
    except Exception as e:
        print(f"Error opening animation: {e}")
        print(f"Please open manually: {file_path}")
        return False


def main():
    """Main function."""
    print("=" * 60)
    print("RFM Architecture Animation Creator")
    print("=" * 60)
    
    # Check if Python is installed
    if not check_python():
        input("Press Enter to exit...")
        return 1
    
    # Install dependencies if needed
    if not os.path.exists("packages_installed.txt"):
        if install_dependencies():
            with open("packages_installed.txt", "w") as f:
                f.write("Packages installed successfully")
        else:
            input("Press Enter to exit...")
            return 1
    
    # Select format
    print("\nSelect output format:")
    print("1. GIF (works everywhere, larger file)")
    print("2. MP4 (better quality, smaller file)")
    
    choice = input("Enter choice (1 or 2) [default: 1]: ").strip()
    
    if choice == "2":
        output_format = "mp4"
    else:
        output_format = "gif"
    
    # Run animation
    print("\n" + "=" * 60)
    output_path = run_animation(output_format)
    print("=" * 60 + "\n")
    
    if not output_path:
        input("Press Enter to exit...")
        return 1
    
    # Ask to open the animation
    open_choice = input("Open the animation? (Y/n): ").strip().lower()
    if open_choice != "n":
        open_animation(output_path)
    
    print("\nDone!")
    input("Press Enter to exit...")
    return 0


# Set default Python command
PYTHON_CMD = "python"

if __name__ == "__main__":
    sys.exit(main())