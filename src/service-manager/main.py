from pathlib import Path
from typing import Optional
import threading
import requests
import subprocess
import webbrowser
import shutil
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from flask import Flask, request, jsonify
import os
import zipfile

import sheet_downloader

# This project expects its running inside a full Unix-like environment: like WSL (Windows Subsystem for Linux) or a real Linux/macOS shell.

script_path = Path(__file__).parent.resolve()
webhook_url = "http://localhost:5678/webhook/trigger"
test_webhook_url = "http://localhost:5678/webhook-test/trigger"
n8n_web_url = "http://localhost:5678"

# Flask app for receiving callbacks from n8n
flask_app = Flask(__name__)
flask_app.logger.disabled = True

# Global reference to GUI
gui_instance = None


def is_docker_running() -> bool:
    """Check if n8n-custom docker container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "n8n-custom" in result.stdout
    except Exception:
        return False


def export_n8n_data() -> tuple[bool, str]:
    """Export n8n data and .env file to a timestamped zip archive.
    
    Returns:
        tuple[bool, str]: (success, file_path_or_error_message)
    """
    try:
        # Check if container is running
        if is_docker_running():
            return False, "Cannot export while n8n container is running. Please stop the container first."
        
        n8n_data_dir = script_path.parent / "docker-n8n" / "n8n-data"
        env_file = script_path.parent / "docker-n8n" / ".env"
        user_data_dir = script_path.parent.parent / "n8n-files" / "user-data"
        
        # Create user-data directory if it doesn't exist
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if n8n-data exists
        if not n8n_data_dir.exists():
            return False, f"n8n-data directory not found: {n8n_data_dir}"
        
        # Count total files first (skip .first_run_done and nodes/*)
        all_files = [
            f for f in n8n_data_dir.rglob('*')
            if f.is_file()
            and f.name != '.first_run_done'
            and 'nodes' not in f.relative_to(n8n_data_dir).parts
        ]
        total_files = len(all_files) + (1 if env_file.exists() else 0)
        
        if total_files == 0:
            return False, "No files found in n8n-data directory"
        
        # Create timestamped archive filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archive_name = f"n8n_export_{timestamp}.zip"
        archive_path = user_data_dir / archive_name
        
        # Create zip archive with progress tracking
        current_file = 0
        last_pct_printed = -1
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add n8n-data directory
            for file_path in all_files:
                arcname = Path("n8n-data") / file_path.relative_to(n8n_data_dir)
                zipf.write(file_path, arcname)
                current_file += 1
                progress = int((current_file / total_files) * 100)
                if (progress % 5 == 0) and (progress != last_pct_printed):  # Print every 5%
                    last_pct_printed = progress
                    print(f"Export progress: {progress}%")
            
            # Add .env file if it exists
            if env_file.exists():
                zipf.write(env_file, ".env")
                current_file += 1
                progress = int((current_file / total_files) * 100)
                if (progress % 5 == 0) and (progress != last_pct_printed):  # Print every 5%
                    last_pct_printed = progress
                    print(f"Export progress: {progress}%")
        
        print(f"Export progress: 100%")
        return True, str(archive_path)
    except PermissionError as e:
        error_msg = f"Permission denied: Files may be locked by the running container. Error: {str(e)}"
        print(f"Export error: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Export failed: {str(e)}"
        print(f"Export error: {error_msg}")
        return False, error_msg


def import_n8n_data(archive_path: Path) -> tuple[bool, str]:
    """Import n8n data and .env file from a zip archive.
    
    Args:
        archive_path: Path to the zip archive to import
        
    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        # Check if container is running
        if is_docker_running():
            return False, "Cannot import while n8n container is running. Please stop the container first."
        
        if not archive_path.exists():
            return False, f"Archive file not found: {archive_path}"
        
        if not zipfile.is_zipfile(archive_path):
            return False, "File is not a valid zip archive"
        
        docker_n8n_dir = script_path.parent / "docker-n8n"
        n8n_data_dir = docker_n8n_dir / "n8n-data"
        env_file = docker_n8n_dir / ".env"
        
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            # Count total files
            total_files = len(zipf.namelist())
            current_file = 0
            
            # Extract all files with progress tracking
            for member in zipf.namelist():
                # Extract n8n-data
                if member.startswith("n8n-data/"):
                    target_path = n8n_data_dir / member[len("n8n-data/"):]
                    if member.endswith('/'):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zipf.open(member) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
                
                # Extract .env
                elif member == ".env":
                    with zipf.open(member) as source, open(env_file, 'wb') as target:
                        target.write(source.read())
                
                current_file += 1
                progress = int((current_file / total_files) * 100)
                last_pct_printed=-1
                if (progress % 5 == 0) and (progress % 5 != last_pct_printed):  # Print every 5%
                    last_pct_printed = progress
                    print(f"Import progress: {progress}%")
            
            print(f"Import progress: 100%")
        
        return True, f"Successfully imported n8n data and .env file from {archive_path.name}"
    except PermissionError as e:
        error_msg = f"Permission denied: Files may be locked by the running container. Error: {str(e)}"
        print(f"Import error: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Import failed: {str(e)}"
        print(f"Import error: {error_msg}")
        return False, error_msg



def create_root_with_sun_valley_theme() -> tk.Tk:
    """Create a Tk root and apply Sun Valley theme if available.

    Preference order:
    1) TKinterModernThemes (Sun Valley) if installed
    2) sv_ttk (Sun Valley) if installed
    3) Default Tk theme as fallback
    """
    # Try TKinterModernThemes first
    try:
        # ThemedTk is a Tk subclass that applies the chosen theme
        from tkintermodernthemes import ThemedTk  # type: ignore
        root = ThemedTk(theme="sun-valley")
        return root
    except Exception:
        pass

    # Fallback to sv_ttk (Sun Valley ttk theme)
    root = tk.Tk()
    try:
        import sv_ttk  # type: ignore
        # Use light variant by default; change to "dark" if preferred
        sv_ttk.set_theme("light")
    except Exception:
        # No modern theme available; continue with default ttk
        pass
    return root

@flask_app.route('/callback/results', methods=['POST'])
def handle_results():
    """Handle results POST from n8n workflow"""
    data = request.get_json()
    if gui_instance:
        gui_instance.handle_n8n_callback(data)
    return jsonify({"status": "received"}), 200


class ServiceManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Service Manager - n8n Workflow Controller")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # State variables
        self.download_thread = None
        self.output_directory = None
        self.processing = False
        
        # Setup GUI
        self.setup_gui()
        
        # Start checking docker status
        self.check_docker_status()
        
    def setup_gui(self):
        """Create all GUI elements"""
        
        # Docker Control Section
        docker_frame = ttk.LabelFrame(self.root, text="Docker n8n Container Control", padding=10)
        docker_frame.pack(fill="x", padx=10, pady=5)
        
        self.docker_status_label = ttk.Label(docker_frame, text="Status: Checking...", font=("Arial", 10))
        self.docker_status_label.pack(side="left", padx=5)
        
        self.docker_btn = ttk.Button(docker_frame, text="Start Container", command=self.toggle_docker, width=20)
        self.docker_btn.pack(side="left", padx=5)
        
        self.open_n8n_btn = ttk.Button(docker_frame, text="Open n8n Web UI", command=self.open_n8n_web, width=20)
        self.open_n8n_btn.pack(side="left", padx=5)
        
        # File Input Section
        input_frame = ttk.LabelFrame(self.root, text="File Input", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Google Sheets URL
        sheets_frame = ttk.Frame(input_frame)
        sheets_frame.pack(fill="x", pady=5)
        
        ttk.Label(sheets_frame, text="Google Sheets URL:").pack(side="left", padx=5)
        self.sheets_url_entry = ttk.Entry(sheets_frame, width=50)
        self.sheets_url_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.download_btn = ttk.Button(sheets_frame, text="Download & Process", command=self.download_from_sheets, width=20)
        self.download_btn.pack(side="left", padx=5)
        
        # Local File
        local_frame = ttk.Frame(input_frame)
        local_frame.pack(fill="x", pady=5)
        
        ttk.Label(local_frame, text="Or select local file:").pack(side="left", padx=5)
        self.local_file_btn = ttk.Button(local_frame, text="Browse & Process", command=self.select_local_file, width=20)
        self.local_file_btn.pack(side="left", padx=5)
        
        # Output Directory Section
        output_frame = ttk.LabelFrame(self.root, text="Output Directory", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_label = ttk.Label(output_frame, text="No directory selected", foreground="gray")
        self.output_label.pack(side="left", padx=5, fill="x", expand=True)
        
        self.output_btn = ttk.Button(output_frame, text="Select Directory", command=self.select_output_directory, width=20)
        self.output_btn.pack(side="left", padx=5)
        
        # n8n Data Export/Import Section
        data_frame = ttk.LabelFrame(self.root, text="n8n Data Management", padding=10)
        data_frame.pack(fill="x", padx=10, pady=5)
        
        self.export_btn = ttk.Button(data_frame, text="Export n8n Data", command=self.export_n8n_data_handler, width=20)
        self.export_btn.pack(side="left", padx=5)
        
        self.import_btn = ttk.Button(data_frame, text="Import n8n Data", command=self.import_n8n_data_handler, width=20)
        self.import_btn.pack(side="left", padx=5)
        
        # Status/Log Section
        log_frame = ttk.LabelFrame(self.root, text="Status & Logs", padding=10)
        log_frame.pack(fill="both", padx=10, pady=5, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD, state='disabled')
        self.log_text.pack(fill="both", expand=True)
        
        # Progress Section
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready", font=("Arial", 9, "bold"))
        self.progress_label.pack(side="left", padx=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        
    def log(self, message, level="INFO"):
        """Add message to log display"""
        self.log_text.configure(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        
    def check_docker_status(self):
        """Check if docker container is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_running = "n8n-custom" in result.stdout
            
            if is_running:
                self.docker_status_label.config(text="Status: Running ✓", foreground="green")
                self.docker_btn.config(text="Stop Container")
            else:
                self.docker_status_label.config(text="Status: Not Running", foreground="red")
                self.docker_btn.config(text="Start Container")
                
        except Exception as e:
            self.docker_status_label.config(text="Status: Error", foreground="red")
            self.log(f"Error checking docker status: {e}", "ERROR")
            
        # Schedule next check
        self.root.after(3000, self.check_docker_status)
        
    def toggle_docker(self):
        """Start or stop docker container"""
        self.docker_btn.config(state="disabled")
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_running = "n8n-custom" in result.stdout
            
            if is_running:
                # Stop container
                self.log("Stopping n8n container...")
                self.progress_label.config(text="Stopping container...")
                self.progress_bar.start()
                
                def stop_container():
                    script_path_parent = script_path.parent / "docker-n8n" / "stop-n8n.sh"
                    result = subprocess.run(
                        [str(script_path_parent)],
                        cwd=str(script_path_parent.parent)
                    )
                    
                    def after_stop():
                        self.progress_bar.stop()
                        self.docker_btn.config(state="normal")
                        if result.returncode == 0:
                            self.log("Container stopped successfully")
                            self.progress_label.config(text="Ready")
                        else:
                            self.log(f"Failed to stop container: {result.stderr}", "ERROR")
                            self.progress_label.config(text="Error stopping container")
                        self.check_docker_status()
                    
                    self.root.after(0, after_stop)
                
                threading.Thread(target=stop_container, daemon=True).start()
            else:
                # Start container
                self.log("Starting n8n container...")
                self.progress_label.config(text="Starting container...")
                self.progress_bar.start()
                
                def start_container():
                    script_path_parent = script_path.parent / "docker-n8n" / "start-n8n.sh"
                    result = subprocess.run(
                        [str(script_path_parent)],
                        cwd=str(script_path_parent.parent)
                    )
                    
                    def after_start():
                        self.progress_bar.stop()
                        self.docker_btn.config(state="normal")
                        if result.returncode == 0:
                            self.log("Container started successfully")
                            self.progress_label.config(text="Ready")
                        else:
                            self.log(f"Failed to start container: {result.stderr}", "ERROR")
                            self.progress_label.config(text="Error starting container")
                        self.check_docker_status()
                    
                    self.root.after(0, after_start)
                
                threading.Thread(target=start_container, daemon=True).start()
                
        except Exception as e:
            self.log(f"Error toggling docker: {e}", "ERROR")
            self.docker_btn.config(state="normal")
            self.progress_bar.stop()
            
    def open_n8n_web(self):
        """Open n8n web interface in browser"""
        try:
            sheet_downloader.open_browser(n8n_web_url)
            self.log(f"Opening n8n web interface: {n8n_web_url}")
        except Exception as e:
            self.log(f"Error opening web interface: {e}", "ERROR")
            
    def download_from_sheets(self):
        """Download file from Google Sheets"""
        url = self.sheets_url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a Google Sheets URL")
            return
            
        # Cancel any ongoing download
        if self.download_thread and self.download_thread.is_alive():
            self.log("Cancelling previous download...", "WARN")
            
        self.log(f"Starting download from Google Sheets...")
        self.download_btn.config(state="disabled")
        self.local_file_btn.config(state="disabled")
        
        res, thread = sheet_downloader.download_sheet(url, self.get_file_callback)
        self.download_thread = thread

        if res == 1 and thread:
            self.log("Manual download required - please complete in your browser")
            self.progress_label.config(text="Waiting for download...")
            self.progress_bar.start()
        elif res == 0:
            self.log("File downloaded successfully")
        elif res < 0:
            error_messages = {
                -1: "Invalid Google Sheets URL",
                -2: "Failed to open browser for authentication",
                -3: "HTTP error during download",
                -4: "Network error during download",
                -5: "Timeout during download"
            }
            self.log(f"Download failed: {error_messages.get(res, 'Unknown error')}", "ERROR")
            self.progress_label.config(text=f"Error: {error_messages.get(res, 'Unknown error')}")
            self.progress_bar.stop()
            self.download_btn.config(state="normal")
            self.local_file_btn.config(state="normal")
        else:
            self.log(f"Download failed with error code: {res}", "ERROR")
            self.download_btn.config(state="normal")
            self.local_file_btn.config(state="normal")
            
    def select_local_file(self):
        """Select local XLSX file"""
        # Cancel any ongoing download
        if self.download_thread and self.download_thread.is_alive():
            self.log("Cancelling Google Sheets download...", "WARN")
            
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            self.log(f"Selected file: {file_path}")
            self.get_file_callback(Path(file_path))
            
    def get_file_callback(self, file: Optional[Path]) -> None:
        """Callback when file is obtained (downloaded or selected)"""
        def callback_in_main_thread():
            self.progress_bar.stop()
            self.download_btn.config(state="normal")
            self.local_file_btn.config(state="normal")
            
            if file:
                self.log(f"Processing file: {file}")
                
                # Validate file extension
                if not file.suffix.lower() == ".xlsx":
                    self.log("File does not have .xlsx extension", "ERROR")
                    messagebox.showerror("Invalid File", "The file must be an Excel file (.xlsx)")
                    self.progress_label.config(text="Error: Invalid file type")
                    return
                    
                # Move file to n8n sheets directory
                new_name = f"sheet_{int(time.time())}.xlsx"
                destination = script_path.parent.parent / "n8n-files" / "sheets" / new_name
                
                try:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy instead of rename to avoid cross-device link errors
                    shutil.copy2(str(file), str(destination))
                    if file.parent != destination.parent:
                        file.unlink()  # Remove original if it was copied
                        
                    self.log(f"File moved to: {destination}")
                    
                    # Trigger n8n workflow
                    self.log("Triggering n8n workflow...")
                    self.progress_label.config(text="Processing file...")
                    self.progress_bar.start()
                    self.processing = True
                    
                    try:
                        requests.post(test_webhook_url, json={"filename": new_name, "template": "default.docx"}, timeout=10) # Test webhook
                        response = requests.post(webhook_url, json={"filename": new_name, "template": "default.docx"}, timeout=10)
                        if response.status_code == 200:
                            self.log("Webhook triggered successfully - waiting for results...")
                        else:
                            self.log(f"Failed to trigger webhook. Status code: {response.status_code}", "ERROR")
                            self.progress_bar.stop()
                            self.processing = False
                            self.progress_label.config(text="Error: Webhook failed")
                    except requests.RequestException as e:
                        self.log(f"Error triggering webhook: {e}", "ERROR")
                        self.progress_bar.stop()
                        self.processing = False
                        self.progress_label.config(text="Error: Cannot reach n8n")
                        
                except Exception as e:
                    self.log(f"Error moving file: {e}", "ERROR")
                    messagebox.showerror("Error", f"Failed to process file: {e}")
                    self.progress_label.config(text="Error processing file")
            else:
                self.log("No file was found", "ERROR")
                self.progress_label.config(text="Error: No file")
                
        self.root.after(0, callback_in_main_thread)
        
    def handle_n8n_callback(self, data):
        """Handle callback from n8n with results or errors"""
        def handle_in_main_thread():
            self.progress_bar.stop()
            self.processing = False
            if "error" in data:
                # Error occurred
                error_msg = data.get("error", "Unknown error")
                self.log(f"n8n workflow error: {error_msg}", "ERROR")
                self.progress_label.config(text="Workflow failed")
                messagebox.showerror("Workflow Error", f"n8n workflow failed:\n{error_msg}")
            elif "files" in data:
                # Success - files were generated
                files = data.get("files", [])
                self.log(f"Workflow completed successfully! Generated {len(files)} file(s)")
                
                # Copy files to output directory if specified
                if self.output_directory and files:
                    self.copy_result_files(files)
                else:
                    # Display file locations
                    file_list = "\n".join([f"  - {f}" for f in files])
                    self.log(f"Generated files:\n{file_list}")
                    
                    if not self.output_directory:
                        self.log("No output directory set - files remain in n8n-files/", "WARN")
                        
                self.progress_label.config(text="Workflow completed successfully")
                messagebox.showinfo("Success", f"Workflow completed!\nGenerated {len(files)} file(s)")
            else:
                self.log(f"Received callback with unknown format. Data: {data}", "WARN")
                self.progress_label.config(text="Unknown response")
                
        self.root.after(0, handle_in_main_thread)
        
    def select_output_directory(self):
        """Select output directory for results"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory = Path(directory)
            self.output_label.config(text=str(self.output_directory), foreground="black")
            self.log(f"Output directory set to: {self.output_directory}")
            
    def export_n8n_data_handler(self):
        """Handle n8n data export"""
        self.export_btn.config(state="disabled")
        self.import_btn.config(state="disabled")
        self.progress_label.config(text="Exporting n8n data...")
        self.progress_bar.start()
        
        def export_thread():
            success, result = export_n8n_data()
            
            def after_export():
                self.progress_bar.stop()
                self.export_btn.config(state="normal")
                self.import_btn.config(state="normal")
                
                if success:
                    self.log(f"Export successful: {result}")
                    self.progress_label.config(text="Export completed successfully")
                    messagebox.showinfo("Export Successful", f"n8n data exported to:\n{result}")
                else:
                    self.log(f"Export failed: {result}", "ERROR")
                    self.progress_label.config(text="Export failed")
                    messagebox.showerror("Export Failed", result)
            
            self.root.after(0, after_export)
        
        threading.Thread(target=export_thread, daemon=True).start()
        
    def import_n8n_data_handler(self):
        """Handle n8n data import"""
        file_path = filedialog.askopenfilename(
            title="Select n8n Export Archive",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.import_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.progress_label.config(text="Importing n8n data...")
        self.progress_bar.start()
        
        def import_thread():
            success, result = import_n8n_data(Path(file_path))
            
            def after_import():
                self.progress_bar.stop()
                self.import_btn.config(state="normal")
                self.export_btn.config(state="normal")
                
                if success:
                    self.log(result)
                    self.progress_label.config(text="Import completed successfully")
                    messagebox.showinfo("Import Successful", result)
                else:
                    self.log(f"Import failed: {result}", "ERROR")
                    self.progress_label.config(text="Import failed")
                    messagebox.showerror("Import Failed", result)
            
            self.root.after(0, after_import)
        
        threading.Thread(target=import_thread, daemon=True).start()


    def copy_result_files(self, files): # not tested
        """Copy result files to output directory"""
        if not self.output_directory:
            return
            
        n8n_app_dir = script_path.parent.parent / "n8n-files"
        copied_files = []
        
        for file_rel_path in files:
            try:
                # remove n8n files prefix if present
                if file_rel_path.startswith("/files/"):
                    file_rel_path = file_rel_path[len("/files/"):]
                source = n8n_app_dir / file_rel_path
                if source.exists():
                    dest = self.output_directory / source.name
                    shutil.copy2(str(source), str(dest))
                    copied_files.append(dest.name)
                    self.log(f"Copied: {source.name} -> {dest}")
                else:
                    self.log(f"File not found: {source}", "WARN")
            except Exception as e:
                self.log(f"Error copying {file_rel_path}: {e}", "ERROR")
                
        if copied_files:
            file_list = "\n".join([f"  - {f}" for f in copied_files])
            self.log(f"Successfully copied {len(copied_files)} file(s) to output directory:\n{file_list}")


def run_flask():
    """Run Flask server in background thread"""
    flask_app.run(host='0.0.0.0', port=5679, debug=False, use_reloader=False)


def main() -> None:
    global gui_instance
    
    # Start Flask server in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Create and run GUI (apply Sun Valley theme when available)
    root = create_root_with_sun_valley_theme()
    gui_instance = ServiceManagerGUI(root)
    
    root.mainloop()


if __name__ == "__main__":
    main()