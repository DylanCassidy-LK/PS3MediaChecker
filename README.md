# PS3MediaChecker

**PS3MediaChecker** is a Python-based tool designed to help you quickly check and convert video files for compatibility with the PlayStation 3. This user-friendly application scans folders for media files, identifies whether they are supported by the PS3, and offers an option to automatically convert unsupported files to a PS3-compatible format using `ffmpeg`.

## Key Features

- **File Compatibility Check**: Easily scan folders to check if your video files are compatible with the PS3.
- **Automatic Conversion**: Convert unsupported files to PS3-friendly formats with a single click.
- **Real-time Feedback**: Monitor progress with an animated progress bar and real-time file processing updates.
- **Detailed Logs**: View a summary of results, with the option to dive deeper into detailed logs.
- **Standalone Executable**: Package the app as a standalone executable for easy distribution and use on Windows, macOS, and Linux.


## How to Use: Clone the Repository: `git clone https://github.com/yourusername/PS3MediaChecker.git`. Install Dependencies: Ensure you have `ffmpeg` installed and available in your system's PATH. Run the Application: `python ps3mediachecker.py`. Package as Executable: Use PyInstaller to create standalone executables: `pyinstaller --onefile --windowed ps3mediachecker.py`. Select a Folder: Choose the folder containing your video files and start the scan. Optionally, choose to convert unsupported files to a PS3-compatible format.


