import os
import time
import threading
from tkinter import Tk, StringVar, Label, Button, Entry, filedialog, ttk, Text, Scrollbar, END
from concurrent.futures import ThreadPoolExecutor

# ========================== CONFIG ==========================
CHUNK_SIZE = 128 * 1024 * 1024  # 128 MB
MAX_WORKERS = 64
# ===========================================================

copied_size = 0
total_size = 0
lock = threading.Lock()
is_copying = False

def get_total_size(dir_path):
    total = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total

def copy_file(src, dst):
    global copied_size
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        while True:
            chunk = fsrc.read(CHUNK_SIZE)
            if not chunk:
                break
            fdst.write(chunk)
            with lock:
                copied_size += len(chunk)

def start_copy():
    global copied_size, total_size, is_copying
    
    source = source_var.get().strip()
    dest = dest_var.get().strip()
    
    if not source or not dest:
        log("❌ Please select both Source and Destination folders")
        return
    if not os.path.exists(source):
        log("❌ Source folder doesn't exist!")
        return
    
    if is_copying:
        log("⚠️ Copy is already running...")
        return

    is_copying = True
    copied_size = 0
    start_btn.config(state="disabled")
    
    log("🔍 Calculating total size...")
    total_size = get_total_size(source)
    log(f"📦 Total size: {total_size / (1024**3):.2f} GB")
    log("🚀 Starting copy... (Safe mode - originals not deleted)\n")

    threading.Thread(target=run_copy, args=(source, dest), daemon=True).start()

def run_copy(source, dest):
    global copied_size
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for root, dirs, files in os.walk(source):
            rel_root = os.path.relpath(root, source)
            dest_root = os.path.join(dest, rel_root) if rel_root != "." else dest
            os.makedirs(dest_root, exist_ok=True)

            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(dest_root, file)
                executor.submit(copy_file, src, dst)

    # Final message
    total_time = (time.time() - start_time) / 60
    avg_speed = (total_size / (time.time() - start_time)) / (1024*1024)
    
    log(f"\n✅ COPY COMPLETED SUCCESSFULLY!")
    log(f"⏱️  Total time: {total_time:.1f} minutes")
    log(f"⚡ Average speed: {avg_speed:.1f} MB/s")
    log("🎉 Your original files are safe. You can delete them manually if you want.")
    
    start_btn.config(state="normal")
    global is_copying
    is_copying = False

def log(message):
    log_text.config(state="normal")
    log_text.insert(END, message + "\n")
    log_text.see(END)
    log_text.config(state="disabled")

def browse_source():
    path = filedialog.askdirectory(title="Select Source Folder")
    if path:
        source_var.set(path)

def browse_dest():
    path = filedialog.askdirectory(title="Select Destination Folder")
    if path:
        dest_var.set(path)

# ========================== GUI ==========================
root = Tk()
root.title("Fast Folder Copier")
root.geometry("780x580")
root.resizable(True, True)

source_var = StringVar()
dest_var = StringVar()

# Title
Label(root, text="Fast & Safe Folder Copier", font=("Helvetica", 16, "bold")).pack(pady=15)

# Source
Label(root, text="Source Folder:", font=("Helvetica", 10)).pack(anchor="w", padx=20)
source_frame = ttk.Frame(root)
source_frame.pack(fill="x", padx=20, pady=5)
Entry(source_frame, textvariable=source_var, width=70).pack(side="left", padx=(0,5))
Button(source_frame, text="Browse", command=browse_source).pack(side="left")

# Destination
Label(root, text="Destination Folder:", font=("Helvetica", 10)).pack(anchor="w", padx=20, pady=(15,0))
dest_frame = ttk.Frame(root)
dest_frame.pack(fill="x", padx=20, pady=5)
Entry(dest_frame, textvariable=dest_var, width=70).pack(side="left", padx=(0,5))
Button(dest_frame, text="Browse", command=browse_dest).pack(side="left")

# Start Button
start_btn = Button(root, text="🚀 START COPYING", font=("Helvetica", 12, "bold"), 
                   bg="#0066cc", fg="white", height=2, command=start_copy)
start_btn.pack(pady=25)

# Progress / Log Area
Label(root, text="Log & Progress:", font=("Helvetica", 10)).pack(anchor="w", padx=20)
log_frame = ttk.Frame(root)
log_frame.pack(fill="both", expand=True, padx=20, pady=5)

scrollbar = Scrollbar(log_frame)
scrollbar.pack(side="right", fill="y")

log_text = Text(log_frame, height=18, state="disabled", wrap="word", font=("Consolas", 9))
log_text.pack(fill="both", expand=True)
scrollbar.config(command=log_text.yview)
log_text.config(yscrollcommand=scrollbar.set)

# Footer
Label(root, text="Safe Copy • Nothing gets deleted from source • Made for big transfers", 
      fg="gray").pack(pady=10)

root.mainloop()
