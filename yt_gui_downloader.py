import customtkinter as ctk
import yt_dlp
import threading
import requests
from PIL import Image, ImageTk
from io import BytesIO
import os
from tkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

download_path = os.path.expanduser("~/Downloads")

app = ctk.CTk()
app.geometry("700x750")
app.title("YouTube Downloader")

# ---------- LOG ----------
def log(msg):
    output.configure(state="normal")
    output.insert("end", msg + "\n")
    output.see("end")
    output.configure(state="disabled")

# ---------- SELECT FOLDER ----------
def choose_folder():
    global download_path
    folder = filedialog.askdirectory()
    if folder:
        download_path = folder
        log(f"Folder: {folder}")

# ---------- FETCH INFO ----------
def fetch_info():
    url = url_entry.get()
    if not url:
        log("Enter URL")
        return

    try:
        ydl = yt_dlp.YoutubeDL()
        info = ydl.extract_info(url, download=False)

        video_title.configure(text=info.get("title", ""))

        thumb = info.get("thumbnail")
        if thumb:
            img = Image.open(BytesIO(requests.get(thumb).content))
            img = img.resize((320, 180))
            img = ImageTk.PhotoImage(img)
            thumb_label.configure(image=img)
            thumb_label.image = img

    except Exception as e:
        log(str(e))

# ---------- DOWNLOAD ----------
def download():
    url = url_entry.get()
    quality = quality_var.get()
    start = start_entry.get()
    end = end_entry.get()

    if not url:
        log("Enter URL")
        return

    # ✅ RESET FIX
    progress_bar.set(0)
    progress_text.configure(text="0%")
    status.configure(text="Starting...")
    app.update_idletasks()

    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            if total:
                progress = downloaded / total
                progress_bar.set(progress * 0.9)   # 0–90%
                percent = int(progress * 90)
                progress_text.configure(text=f"{percent}%")

            status.configure(
                text=f"{round(speed/1024/1024,2)} MB/s • ETA {eta}s"
            )

            app.update_idletasks()

        elif d['status'] == 'finished':
            progress_bar.set(0.95)
            progress_text.configure(text="Merging...")
            status.configure(text="Processing video...")

    def run():
        try:
            if quality == "Best":
                fmt = "bv*+ba/b"
            elif quality == "Audio":
                fmt = "bestaudio"
            else:
                h = quality.replace("p", "")
                fmt = f"bv*[height={h}]+ba/b"

            ydl_opts = {
                "format": fmt,
                "outtmpl": os.path.join(download_path, "%(playlist_title)s/%(title)s.%(ext)s"),
                "merge_output_format": "mp4",
                "progress_hooks": [hook],
                "noplaylist": not playlist_var.get(),
            }

            if start and end:
                ydl_opts["playlist_items"] = f"{start}-{end}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # ✅ FINAL COMPLETE
            progress_bar.set(1)
            progress_text.configure(text="100%")
            status.configure(text="Download Complete ✅")
            log("Download finished")

        except Exception as e:
            log(str(e))

    threading.Thread(target=run).start()

# ---------- UI ----------

title = ctk.CTkLabel(app, text="YouTube Downloader", font=("Arial", 20, "bold"))
title.pack(pady=10)

# URL
url_frame = ctk.CTkFrame(app)
url_frame.pack(pady=10)

url_entry = ctk.CTkEntry(url_frame, width=450, placeholder_text="Paste URL")
url_entry.pack(side="left", padx=10)

paste_btn = ctk.CTkButton(url_frame, text="Paste",
                         command=lambda: url_entry.insert(0, app.clipboard_get()))
paste_btn.pack(side="left")

# Fetch
fetch_btn = ctk.CTkButton(app, text="Fetch Info", command=fetch_info)
fetch_btn.pack(pady=5)

video_title = ctk.CTkLabel(app, text="")
video_title.pack(pady=5)

thumb_label = ctk.CTkLabel(app, text="")
thumb_label.pack()

# Options
options = ctk.CTkFrame(app)
options.pack(pady=10)

quality_var = ctk.StringVar(value="Best")
quality_menu = ctk.CTkOptionMenu(options, variable=quality_var,
                                values=["Best", "1080p", "720p", "480p", "Audio"])
quality_menu.grid(row=0, column=0, padx=10)

playlist_var = ctk.BooleanVar()
playlist_check = ctk.CTkCheckBox(options, text="Playlist", variable=playlist_var)
playlist_check.grid(row=0, column=1)

start_entry = ctk.CTkEntry(options, width=70, placeholder_text="Start")
start_entry.grid(row=0, column=2)

end_entry = ctk.CTkEntry(options, width=70, placeholder_text="End")
end_entry.grid(row=0, column=3)

folder_btn = ctk.CTkButton(app, text="Select Folder", command=choose_folder)
folder_btn.pack(pady=5)

# Download
download_btn = ctk.CTkButton(app, text="Download", height=40, command=download)
download_btn.pack(pady=10)

# Progress
progress_bar = ctk.CTkProgressBar(app, width=500)
progress_bar.set(0)   # ✅ CRITICAL FIX
progress_bar.pack(pady=5)

progress_text = ctk.CTkLabel(app, text="0%")
progress_text.pack()

status = ctk.CTkLabel(app, text="Ready")
status.pack()

# Logs
output = ctk.CTkTextbox(app, width=600, height=150)
output.pack(pady=10)
output.configure(state="disabled")

app.mainloop()