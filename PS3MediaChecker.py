import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import time
import concurrent.futures

class PS3VideoConverter:
    def __init__(self):
        self.active_ffmpeg_processes = []
        self.selected_file = None
        self.selected_folder = None
        self.output_window = None
        self.output_text = None

        # Create the root window first
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window until we're ready to show it

        # Now we can create Tkinter variables
        self.convert_unsupported = tk.BooleanVar()

        # Check if ffmpeg is installed
        if not self.check_ffmpeg_installed():
            self.root.destroy()  # Close the root window if ffmpeg is not installed
            return

        # Create the GUI
        self.create_gui()

    def check_ffmpeg_installed(self):
        """Check if ffmpeg/ffprobe is installed."""
        try:
            subprocess.check_output(["ffmpeg", "-version"])
            subprocess.check_output(["ffprobe", "-version"])
        except FileNotFoundError:
            messagebox.showerror(
                "ffmpeg Not Found",
                "ffmpeg is not installed or not in the system's PATH.\n\n"
                "Please install ffmpeg before using this application."
            )
            return False
        return True

    def create_ffmpeg_output_window(self):
        """Create a new window for FFmpeg output."""
        self.output_window = tk.Toplevel()
        self.output_window.title("FFmpeg Output")
        self.output_window.geometry("600x400")

        self.output_text = scrolledtext.ScrolledText(
            self.output_window, wrap=tk.WORD, bg="#B2DFDB", fg="black", state=tk.NORMAL
        )
        self.output_text.pack(expand=True, fill=tk.BOTH)

    def show_ffmpeg_output_window(self):
        """Create and display the FFmpeg output window when button is pressed."""
        if self.output_window is None or not self.output_window.winfo_exists():
            self.create_ffmpeg_output_window()

    def read_ffmpeg_output(self, ffmpeg_process):
        """Read and display FFmpeg output in the output text widget."""
        try:
            for line in ffmpeg_process.stdout:
                if self.output_text and self.output_text.winfo_exists():
                    self.output_text.configure(state=tk.NORMAL)
                    self.output_text.insert(tk.END, line)
                    self.output_text.configure(state=tk.DISABLED)
                    self.output_text.yview(tk.END)
        except tk.TclError:
            pass  # Ignore any errors if the output_text widget is destroyed

    def convert_to_ps3_compatible(self, input_file, output_file):
        """Convert a file to a PS3-compatible format using ffmpeg."""
        try:
            if not os.path.isfile(input_file):
                if self.text_widget:
                    self.text_widget.insert(tk.END, f"Input file not found: {input_file}\n", "error")
                return False

            # Construct the FFmpeg command with the corrected scale filter
            output_file_ps3 = f"{os.path.splitext(output_file)[0]}_PS3.mp4"
            ffmpeg_cmd = [
                "ffmpeg", "-i", input_file,
                "-vcodec", "h264", "-b:v", "1500k",
                "-profile:v", "main", "-level", "4.1",
                "-acodec", "aac", "-b:a", "192k",
                # Here is the updated scale filter to ensure width is divisible by 2
                "-vf", "scale='trunc(iw/2)*2':'trunc(ih/2)*2'",
                "-movflags", "faststart",
                "-y", output_file_ps3
            ]

            if self.text_widget:
                self.text_widget.insert(tk.END, f"Starting conversion: {input_file} -> {output_file_ps3}\n", "convert")

            ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
            )

            self.active_ffmpeg_processes.append(ffmpeg_process)

           # Show FFmpeg output window if it's not open
            self.show_ffmpeg_output_window()

            # Start reading the FFmpeg output
            threading.Thread(target=self.read_ffmpeg_output, args=(ffmpeg_process,), daemon=True).start()

            ffmpeg_process.wait()

            if ffmpeg_process.returncode == 0 and os.path.isfile(output_file_ps3):
                return True
            else:
               if self.text_widget:
                    self.text_widget.insert(tk.END, f"Conversion failed: {input_file}\n", "error")
            return False

        except subprocess.CalledProcessError as e:
            if self.text_widget:
                self.text_widget.insert(tk.END, f"Conversion error: {str(e)}\n", "error")
            return False




    def start_conversion(self, input_file, output_file):
        """Start conversion process and track it."""
        success = self.convert_to_ps3_compatible(input_file, output_file)
        if success:
            self.text_widget.insert(tk.END, f"Conversion successful: {output_file}\n", "success")
        else:
            self.text_widget.insert(tk.END, f"Conversion failed: {input_file}\n", "error")

    def start_conversion_thread(self, input_file=None):
        """Start the conversion process for the selected file in a new thread."""
        if input_file is None:
            input_file = self.selected_file

        if input_file:
            output_file = f"{os.path.splitext(input_file)[0]}_PS3.mp4"
            threading.Thread(target=self.start_conversion, args=(input_file, output_file), daemon=True).start()
        else:
            self.text_widget.insert(tk.END, "No file selected for conversion.\n", "error")

    def select_file(self):
        """Allow the user to select a file for conversion."""
        self.selected_file = filedialog.askopenfilename()
        if self.selected_file:
            self.text_widget.insert(tk.END, f"Selected file: {self.selected_file}\n", "info")
        else:
            self.text_widget.insert(tk.END, "No file selected.\n", "info")

    def select_folder(self):
        """Allow the user to select a folder for scanning."""
        self.selected_folder = filedialog.askdirectory()
        if self.selected_folder:
            self.text_widget.insert(tk.END, f"Selected folder: {self.selected_folder}\n", "info")
        else:
            self.text_widget.insert(tk.END, "No folder selected.\n", "info")

    def cleanup(self):
        """Cleanup function to terminate FFmpeg processes and close the application."""
        try:
            for ffmpeg_process in self.active_ffmpeg_processes:
                if ffmpeg_process.poll() is None:
                    ffmpeg_process.terminate()  # Terminate the FFmpeg process if it is still running
                    ffmpeg_process.wait()       # Wait for FFmpeg to fully terminate
        except Exception:
            pass
        finally:
            self.root.destroy()

    def scan_folder(self, folder_path, convert=False):
        """Scan folder for PS3 compatible videos and optionally convert unsupported ones."""
        self.text_widget.delete(1.0, tk.END)  # Clear previous output
    
        supported_files = []
        unsupported_files = []
        failed_files = []
    
        files = []
        for root_dir, _, file_names in os.walk(folder_path):
            for file in file_names:
                full_path = os.path.join(root_dir, file)
                files.append(full_path)

        self.progress_bar["maximum"] = len(files)
        self.progress_bar["value"] = 0

        total_files = len(files)
    
        for i, file_path in enumerate(files, start=1):
            video_codec, audio_codec, resolution = self.get_file_info(file_path)
            if video_codec and audio_codec and resolution:
                if self.is_ps3_supported(video_codec, audio_codec, resolution):
                    supported_files.append(file_path)
                else:
                    unsupported_files.append(file_path)
                    if convert:
                        # Convert one file at a time
                        success = self.convert_to_ps3_compatible(file_path, file_path)
                        if success:
                            self.text_widget.insert(tk.END, f"Conversion successful: {file_path}\n", "success")
                        else:
                            self.text_widget.insert(tk.END, f"Conversion failed: {file_path}\n", "error")
            else:
                failed_files.append(file_path)

            # Update real-time progress
            self.text_widget.insert(tk.END, f"Processing file {i}/{total_files}: {file_path}\n")
            self.text_widget.yview(tk.END)  # Auto-scroll to the end of the text widget
            self.text_widget.update_idletasks()

            # Update the progress bar
            self.progress_bar["value"] = i
            self.progress_bar.update_idletasks()

        # Display the summary in the main window
        self.text_widget.insert(tk.END, "\nSummary of Results:\n", "summary")
        self.text_widget.insert(tk.END, f"Supported Files ({len(supported_files)}):\n", "summary")
        for file in supported_files:
            self.text_widget.insert(tk.END, f" - {file}\n", "success")

        self.text_widget.insert(tk.END, f"\nUnsupported Files ({len(unsupported_files)}):\n", "summary")
        for file in unsupported_files:
            self.text_widget.insert(tk.END, f" - {file}\n", "error")

        if failed_files:
            self.text_widget.insert(tk.END, f"\nFailed to Process Files ({len(failed_files)}):\n", "summary")
            for file in failed_files:
                self.text_widget.insert(tk.END, f" - {file}\n", "error")

            self.text_widget.insert(tk.END, "\nScan Complete!\n", "complete")
            self.text_widget.yview_moveto(0)  # Scroll to the top of the text widget


    def start_scan_thread(self):
        """Start the scanning process for the selected folder in a new thread."""
        if self.selected_folder:
            convert = self.convert_unsupported.get()
            threading.Thread(target=self.scan_folder, args=(self.selected_folder, convert), daemon=True).start()
        else:
            self.text_widget.insert(tk.END, "No folder selected for scanning.\n", "error")

    def get_file_info(self, file_path):
        """Get video codec, audio codec, and resolution of the file using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            output = subprocess.check_output(cmd, universal_newlines=True)
            video_info = output.strip().split('\n')

            if len(video_info) >= 3:
                video_codec, width, height = video_info[:3]
            else:
                return None, None, None

            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            output = subprocess.check_output(cmd, universal_newlines=True)
            audio_codec = output.strip()

            resolution = (int(width), int(height))

            return video_codec, audio_codec, resolution
        except Exception as e:
            return None, None, None

    def is_ps3_supported(self, video_codec, audio_codec, resolution):
        """Check if the file is PS3 compatible based on codecs and resolution."""
        max_width, max_height = 1920, 1080
        if video_codec.lower() == "h264" and audio_codec.lower() == "aac":
            if resolution[0] <= max_width and resolution[1] <= max_height:
                return True
        return False

    def create_gui(self):
        """Create the main GUI for the PS3 Compatibility Checker."""
        self.root.deiconify()  # Now we can show the root window
        self.root.title("PS3 Video Compatibility Checker")
        self.root.geometry("800x600")
        self.root.configure(bg="#008080")  # Set background color to teal

        # Use tk.Frame to allow background color customization
        frame = tk.Frame(self.root, bg="#008080", padx=20, pady=20)
        frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Set style for header label
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Header.TLabel', background='#008080', foreground='white', font=("Arial", 18, "bold"))

        label = ttk.Label(
            frame, text="PS3 Video Compatibility Checker", anchor="center", style='Header.TLabel'
        )
        label.grid(row=0, column=0, pady=10)

        # Frame for buttons
        button_frame = tk.Frame(frame, bg="#008080")
        button_frame.grid(row=1, column=0, pady=10)

        # Button to select a file for conversion
        select_button = ttk.Button(button_frame, text="Select File", command=self.select_file)
        select_button.grid(row=0, column=0, padx=5, pady=5)

        # Button to start the conversion process
        convert_button = ttk.Button(button_frame, text="Convert File", command=self.start_conversion_thread)
        convert_button.grid(row=0, column=1, padx=5, pady=5)

        # Button to select a folder for scanning
        select_folder_button = ttk.Button(button_frame, text="Select Folder", command=self.select_folder)
        select_folder_button.grid(row=1, column=0, padx=5, pady=5)

        # Button to start the scanning process
        scan_button = ttk.Button(button_frame, text="Scan Folder", command=self.start_scan_thread)
        scan_button.grid(row=1, column=1, padx=5, pady=5)

        # Checkbox to decide whether to convert unsupported files
        convert_checkbox = ttk.Checkbutton(
            button_frame, text="Convert Unsupported Files", variable=self.convert_unsupported
        )
        convert_checkbox.grid(row=2, column=0, columnspan=2, pady=5)

        # Button to show FFmpeg output window
        output_button = ttk.Button(button_frame, text="Show FFmpeg Output", command=self.show_ffmpeg_output_window)
        output_button.grid(row=3, column=0, columnspan=2, pady=5)

        # Scrollable text widget for logging
        self.text_widget = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, bg="#B2DFDB", fg="black", state=tk.NORMAL, font=("Arial", 10)
        )
        self.text_widget.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Progress bar for file processing
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=400)
        self.progress_bar.grid(row=3, column=0, pady=10)

        # Configure text tags for styling
        self.text_widget.tag_configure("error", foreground="#C62828")  # Dark Red
        self.text_widget.tag_configure("success", foreground="#2E7D32")  # Dark Green
        self.text_widget.tag_configure("info", foreground="#008B8B")  # Dark Cyan
        self.text_widget.tag_configure("summary", foreground="#6A1B9A", font=("Arial", 12, "bold"))  # Purple
        self.text_widget.tag_configure("complete", foreground="#2E7D32", font=("Arial", 12, "bold"))  # Dark Green
        self.text_widget.tag_configure("convert", foreground="#EF6C00")  # Orange

        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.mainloop()

if __name__ == "__main__":
    PS3VideoConverter()
