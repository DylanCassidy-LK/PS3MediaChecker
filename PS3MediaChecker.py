import os
import subprocess
import threading
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

def check_ffmpeg_installed():
    """Check if ffmpeg/ffprobe is installed."""
    try:
        subprocess.check_output(["ffmpeg", "-version"])
    except FileNotFoundError:
        messagebox.showerror(
            "ffmpeg Not Found",
            "ffmpeg is not installed or not in the system's PATH.\n\n"
            "Please install ffmpeg before using this application.\n\n"
            "Installation instructions:\n"
            "- Windows: Download from https://ffmpeg.org/download.html and add to PATH.\n"
            "- macOS: Install via Homebrew with `brew install ffmpeg`.\n"
            "- Linux: Install via your package manager (e.g., `sudo apt-get install ffmpeg`)."
        )
        return False
    return True

def get_file_info(file_path):
    """Extract video and audio codec information and resolution using ffprobe."""
    try:
        video_codec = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        ).decode().strip()

        audio_codec = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        ).decode().strip()

        resolution = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", file_path]
        ).decode().strip()

        return video_codec, audio_codec, resolution
    except subprocess.CalledProcessError:
        return None, None, None

def is_ps3_supported(video_codec, audio_codec, resolution):
    """Check if the file is PS3 supported based on codec and resolution."""
    if video_codec in ['h264', 'mpeg4'] and audio_codec == 'aac':
        width, height = map(int, resolution.split('x'))
        if width <= 1920 and height <= 1080:
            return True
    return False

def get_video_duration(file_path):
    """Get the duration of the video file in seconds using ffprobe."""
    try:
        duration_str = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        ).decode().strip()
        return float(duration_str)
    except subprocess.CalledProcessError:
        return None

def convert_to_ps3_compatible(input_file, output_file, progress_callback=None):
    """Convert a file to a PS3-compatible format using ffmpeg."""
    duration = get_video_duration(input_file)
    if duration is None:
        return False
    
    try:
        process = subprocess.Popen(
            ["ffmpeg", "-i", input_file, "-vcodec", "h264", "-acodec", "aac", output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        # Monitor progress
        for line in process.stdout:
            if progress_callback:
                # Extract time from the output
                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
                if time_match:
                    hours, minutes, seconds, _ = map(int, time_match.groups())
                    elapsed_time = hours * 3600 + minutes * 60 + seconds
                    progress = elapsed_time / duration
                    progress_callback(progress)

        process.wait()

        if process.returncode == 0:
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False


def update_progress_bar(progress_bar, progress):
    """Update the progress bar with the given progress value (0 to 1)."""
    progress_bar.after(0, lambda: progress_bar.config(value=progress * 100))



def start_conversion_thread(files_to_convert, text_widget, progress_bar):
    """Start a thread to handle file conversion."""
    def conversion_task():
        for i, file_path in enumerate(files_to_convert):
            output_file = os.path.splitext(file_path)[0] + "_ps3.mp4"
            
            # Check if the converted file already exists
            if os.path.exists(output_file):
                text_widget.insert(tk.END, f"Skipping: {file_path} (already converted)\n", "skip")
                continue
            
            text_widget.insert(tk.END, f"Converting: {file_path}\n", "convert" , " This may take a while.")
            
            if convert_to_ps3_compatible(file_path, output_file, lambda p: update_progress_bar(progress_bar, p)):
                text_widget.insert(tk.END, f"Converted: {file_path} to {output_file}\n", "convert")
                text_widget.insert(tk.END, f"Converted file located at: {output_file}\n", "convert")
            else:
                text_widget.insert(tk.END, f"Failed to convert: {file_path}\n", "error")

            text_widget.yview(tk.END)
            text_widget.update()

            progress_bar["value"] = 0  # Reset for the next file

        text_widget.insert(tk.END, "\nConversion Complete!\n", "complete")
        text_widget.yview(tk.END)

    conversion_thread = threading.Thread(target=conversion_task)
    conversion_thread.start()

def scan_folder(folder_path, text_widget, progress_bar, convert=False):
    """Scan folder for PS3 compatible videos and optionally convert unsupported ones."""
    text_widget.delete(1.0, tk.END)  # Clear previous output
    
    supported_files = []
    unsupported_files = []
    failed_files = []
    
    files = []
    for root, _, file_names in os.walk(folder_path):
        for file in file_names:
            files.append(os.path.join(root, file))

    progress_bar["maximum"] = len(files)

    detailed_logs = ""  # For accumulating detailed logs
    total_files = len(files)
    
    for i, file_path in enumerate(files):
        video_codec, audio_codec, resolution = get_file_info(file_path)
        if video_codec and audio_codec and resolution:
            if is_ps3_supported(video_codec, audio_codec, resolution):
                supported_files.append(file_path)
            else:
                unsupported_files.append(file_path)
        else:
            failed_files.append(file_path)

        # Update real-time progress
        text_widget.insert(tk.END, f"Processing file {i+1}/{total_files}: {file_path}\n")
        detailed_logs += f"{file_path} - Video Codec: {video_codec}, Audio Codec: {audio_codec}, Resolution: {resolution}\n"
        text_widget.yview(tk.END)  # Auto-scroll to the end of the text widget
        text_widget.update()

        # Update the progress bar
        progress_bar["value"] = i + 1
        progress_bar.update()

    # Notify user about unsupported files before conversion
    if unsupported_files and convert:
        text_widget.insert(tk.END, "\nUnsupported files found! Starting conversion...\n", "convert")
        text_widget.yview(tk.END)
        text_widget.update()
        start_conversion_thread(unsupported_files, text_widget, progress_bar)

    # Clear the processing output
    text_widget.delete(1.0, tk.END)
    
    # Display the summary in the main window
    text_widget.insert(tk.END, "Summary of Results:\n", "summary")
    text_widget.insert(tk.END, f"Supported Files ({len(supported_files)}):\n", "summary")
    for file in supported_files:
        text_widget.insert(tk.END, f" - {file}\n", "success")

    text_widget.insert(tk.END, f"\nUnsupported Files ({len(unsupported_files)}):\n", "summary")
    for file in unsupported_files:
        text_widget.insert(tk.END, f" - {file}\n", "error")

    if failed_files:
        text_widget.insert(tk.END, f"\nFailed to Process Files ({len(failed_files)}):\n", "summary")
        for file in failed_files:
            text_widget.insert(tk.END, f" - {file}\n", "error")

    text_widget.yview_moveto(0)  # Scroll to the top of the text widget

    # After scanning, provide feedback and the option to view detailed logs
    text_widget.insert(tk.END, "\nScan Complete!\n", "complete")

    details_button = ttk.Button(frame, text="View Details", command=lambda: show_details(detailed_logs))
    details_button.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

def show_details(details):
    """Show detailed logs in a new window."""
    detail_window = tk.Toplevel()
    detail_window.title("Detailed Logs")
    detail_text = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD, width=60, height=20)
    detail_text.pack(pady=10, expand=True, fill=tk.BOTH)
    detail_text.insert(tk.END, details)

def select_folder(text_widget, progress_bar, convert=False):
    """Open a folder dialog to select a folder and start scanning."""
    folder_path = filedialog.askdirectory()
    if folder_path:
        scan_folder(folder_path, text_widget, progress_bar, convert)

def create_gui():
    """Create a minimal GUI using tkinter."""
    if not check_ffmpeg_installed():
        return
    
    global root, frame  # Make root accessible to the scan_folder function
    root = tk.Tk()
    root.title("PS3 Video Compatibility Checker")
    root.geometry("860x600")  # Set a wider default window size
    root.resizable(True, True)  # Allow the window to be resizable

    style = ttk.Style()
    style.configure("TButton", font=("Helvetica", 12), padding=10)
    style.configure("TLabel", font=("Helvetica", 14))
    style.configure("TFrame", background="#2c3e50")
    style.configure("TProgressbar", thickness=20, troughcolor="#34495e", background="#1abc9c")
    style.configure("TLabel", background="#2c3e50", foreground="#ecf0f1")
    style.map("TProgressbar",
              background=[('!disabled', '#3498db'), ('active', '#2980b9')])

    frame = ttk.Frame(root, padding=20)
    frame.grid(row=0, column=0, sticky="nsew")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(3, weight=1)

    label = ttk.Label(frame, text="PS3 Video Compatibility Checker")
    label.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

    convert_var = tk.BooleanVar()
    convert_checkbox = ttk.Checkbutton(frame, text="Convert Unsupported Files", variable=convert_var)
    convert_checkbox.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

    select_button = ttk.Button(frame, text="Select Folder", command=lambda: select_folder(text_widget, progress_bar, convert_var.get()))
    select_button.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

    text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, bg="#34495e", fg="#ecf0f1")
    text_widget.grid(row=3, column=0, columnspan=2, pady=10, sticky="nsew")

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progress_bar.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
    
    # Add custom tags for success and error messages
    text_widget.tag_configure("success", foreground="#1abc9c")
    text_widget.tag_configure("error", foreground="#e74c3c")
    text_widget.tag_configure("summary", font=("Helvetica", 12, "bold"), foreground="#ecf0f1")
    text_widget.tag_configure("complete", font=("Helvetica", 12, "bold"), foreground="#2ecc71")
    text_widget.tag_configure("convert", font=("Helvetica", 12, "bold"), foreground="#f1c40f")
    text_widget.tag_configure("skip", foreground="#f39c12")

    root.configure(background="#2c3e50")
    root.mainloop()

if __name__ == "__main__":
    create_gui()
