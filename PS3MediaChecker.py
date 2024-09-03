import os
import subprocess
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

def convert_to_ps3_compatible(input_file, output_file):
    """Convert a file to a PS3-compatible format using ffmpeg."""
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_file, "-vcodec", "h264", "-acodec", "aac", output_file],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

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
                if convert:
                    output_file = os.path.splitext(file_path)[0] + "_ps3.mp4"
                    if convert_to_ps3_compatible(file_path, output_file):
                        text_widget.insert(tk.END, f"Converted: {file_path} to {output_file}\n", "convert")
                        supported_files.append(output_file)
                    else:
                        text_widget.insert(tk.END, f"Failed to convert: {file_path}\n", "error")
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
    root.bell()  # Play a sound

    details_button = ttk.Button(text_widget, text="View Details", command=lambda: show_details(detailed_logs))
    details_button.pack(pady=10)

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
    
    global root  # Make root accessible to the scan_folder function
    root = tk.Tk()
    root.title("PS3 Video Compatibility Checker")
    root.geometry("700x500")  # Set a default window size
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
    frame.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

    label = ttk.Label(frame, text="PS3 Video Compatibility Checker")
    label.pack(pady=10)

    convert_var = tk.BooleanVar()
    convert_checkbox = ttk.Checkbutton(frame, text="Convert Unsupported Files", variable=convert_var)
    convert_checkbox.pack(pady=10)

    select_button = ttk.Button(frame, text="Select Folder", command=lambda: select_folder(text_widget, progress_bar, convert_var.get()))
    select_button.pack(pady=10)

    text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=60, height=20, bg="#34495e", fg="#ecf0f1")
    text_widget.pack(pady=10, expand=True, fill=tk.BOTH)

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progress_bar.pack(pady=10, fill=tk.X)
    
    # Add custom tags for success and error messages
    text_widget.tag_configure("success", foreground="#1abc9c")
    text_widget.tag_configure("error", foreground="#e74c3c")
    text_widget.tag_configure("summary", font=("Helvetica", 12, "bold"), foreground="#ecf0f1")
    text_widget.tag_configure("complete", font=("Helvetica", 12, "bold"), foreground="#2ecc71")
    text_widget.tag_configure("convert", font=("Helvetica", 12, "bold"), foreground="#f1c40f")

    root.configure(background="#2c3e50")
    root.mainloop()

if __name__ == "__main__":
    create_gui()
