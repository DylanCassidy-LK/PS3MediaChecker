diff --git a/PS3MediaChecker.py b/PS3MediaChecker.py
index 229576b6e466518361fc1314ccc142ad305a1b06..b17abe1818d7cdbd751b421ddab55aca3bbcdf6b 100644
--- a/PS3MediaChecker.py
+++ b/PS3MediaChecker.py
@@ -1,49 +1,50 @@
 import os
 import subprocess
 import threading
 import tkinter as tk
 from tkinter import filedialog, messagebox, scrolledtext, ttk
-import time
-import concurrent.futures
 
 class PS3VideoConverter:
     def __init__(self):
         self.active_ffmpeg_processes = []
         self.selected_file = None
         self.selected_folder = None
         self.output_window = None
         self.output_text = None
+        self.startup_failed = False
 
-      self.root = tk.Tk()
+        self.root = tk.Tk()
         self.root.withdraw()  
         
         self.convert_unsupported = tk.BooleanVar()
 
        
         if not self.check_ffmpeg_installed():
-            self.root.destroy()  
+            self.startup_failed = True
+            self.root.destroy()
+            return
 
        
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
@@ -103,51 +104,52 @@ class PS3VideoConverter:
 
             
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
-            self.text_widget.insert(tk.END, f"Conversion successful: {output_file}\n", "success")
+            output_file_ps3 = f"{os.path.splitext(output_file)[0]}_PS3.mp4"
+            self.text_widget.insert(tk.END, f"Conversion successful: {output_file_ps3}\n", "success")
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
@@ -206,52 +208,52 @@ class PS3VideoConverter:
 
             
             self.text_widget.insert(tk.END, f"Processing file {i}/{total_files}: {file_path}\n")
             self.text_widget.yview(tk.END)  
             self.text_widget.update_idletasks()
 
             
             self.progress_bar["value"] = i
             self.progress_bar.update_idletasks()
 
         
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
 
-            self.text_widget.insert(tk.END, "\nScan Complete!\n", "complete")
-            self.text_widget.yview_moveto(0)  
+        self.text_widget.insert(tk.END, "\nScan Complete!\n", "complete")
+        self.text_widget.yview_moveto(0)
 
 
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
