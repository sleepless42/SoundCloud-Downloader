import ctypes
import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, Menu
from yt_dlp import YoutubeDL
import pyperclip
from tkinter import ttk

# ✅ Четкость интерфейса на экранах с высоким DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

CONFIG_FILE = "config.txt"

def load_config():
    config = {"path": "", "flac": False, "meta": False}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PATH="):
                    config["path"] = line.strip().split("=", 1)[1]
                elif line.startswith("FLAC="):
                    config["flac"] = line.strip().split("=", 1)[1] == "True"
                elif line.startswith("METADATA="):
                    config["meta"] = line.strip().split("=", 1)[1] == "True"
    if not config["path"] or not os.path.isdir(config["path"]):
        config["path"] = os.path.join(os.getcwd(), "Downloads")
        os.makedirs(config["path"], exist_ok=True)
    return config

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(f"PATH={download_path}\n")
        f.write(f"FLAC={flac_var.get()}\n")
        f.write(f"METADATA={metadata_var.get()}\n")

config = load_config()
download_path = config["path"]

root = tk.Tk()
root.title("SoundCloud Downloader")
root.geometry("650x330")
root.resizable(False, False)
root.configure(bg="#F5F5F5")

flac_var = tk.BooleanVar(value=config["flac"])
metadata_var = tk.BooleanVar(value=config["meta"])

def update_progress(percent, message=""):
    progress_var.set(percent)
    progress_bar.update()
    progress_status_label.config(text=message)

def download_track():
    url = url_entry.get().strip()
    if not url.startswith("http"):
        messagebox.showerror("Error", "Please enter a valid SoundCloud link.")
        return

    status_label.config(text="")
    progress_frame.pack(pady=10)
    update_progress(0, "🔄 Contacting servers...")
    download_button.config(state="disabled")
    save_config()

    def run_download():
        try:
            format_codec = 'flac' if flac_var.get() else 'mp3'
            quality = '0' if flac_var.get() else '320'

            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [progress_hook],
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': format_codec,
                        'preferredquality': quality,
                    }
                ]
            }

            if metadata_var.get():
                ydl_opts.update({
                    'writethumbnail': True,
                    'writeinfojson': True,
                })
                ydl_opts['postprocessors'] += [
                    {'key': 'EmbedThumbnail'},
                    {'key': 'FFmpegMetadata'}
                ]

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url)
                title = info.get("title", "track")
                json_path = os.path.join(download_path, f"{title}.info.json")
                if os.path.exists(json_path):
                    os.remove(json_path)
                update_progress(100, "✅ Done")
                status_label.config(text=f"✅ Downloaded: {title}.{format_codec}")

        except Exception as e:
            status_label.config(text="❌ Error")
            progress_status_label.config(text="❌ Failed")
            messagebox.showerror("Error", str(e))

        finally:
            download_button.config(state="normal")
            root.after(3000, lambda: progress_frame.pack_forget())

    threading.Thread(target=run_download).start()

def progress_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('_percent_str', '').strip()
        percent = float(downloaded.replace('%', '') or 0)
        update_progress(percent, "⬇️ Downloading...")
    elif d['status'] == 'finished':
        update_progress(100, "🔁 Converting...")

def clear_input():
    url_entry.delete(0, tk.END)
    status_label.config(text="")

def paste_link():
    try:
        url_entry.delete(0, tk.END)
        url_entry.insert(0, pyperclip.paste())
    except:
        messagebox.showerror("Error", "Failed to paste from clipboard.")

def change_download_folder():
    global download_path
    new_path = filedialog.askdirectory(initialdir=download_path, title="Select Download Folder")
    if new_path:
        download_path = new_path
        save_config()
        path_label.config(text=f"📁 Path: {download_path}")

def open_folder(event=None):
    try:
        os.startfile(download_path)
    except Exception as e:
        messagebox.showerror("Error", f"Can't open folder:\n{e}")

# ==== Меню ====
menu_bar = Menu(root, tearoff=0, bg="#F5F5F5", fg="black", relief="flat", activebackground="#E0E0E0", activeforeground="black")
settings_menu = Menu(menu_bar, tearoff=0, bg="#F5F5F5", fg="black", relief="flat", activebackground="#E0E0E0", activeforeground="black")
settings_menu.add_command(label="Change download folder...", command=change_download_folder)
settings_menu.add_checkbutton(label="FLAC format", variable=flac_var, command=save_config)
settings_menu.add_checkbutton(label="Download with metadata", variable=metadata_var, command=save_config)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
root.config(menu=menu_bar)

tk.Label(root, text="Paste a SoundCloud track link:", bg="#F5F5F5", fg="black", font=("Segoe UI", 10)).pack(pady=10)

entry_frame = tk.Frame(root, bg="#F5F5F5")
entry_frame.pack()

url_entry = tk.Entry(entry_frame,
                    width=50,
                    font=("Segoe UI", 10),
                    bg="#FFFFFF",
                    fg="black",
                    bd=1,
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground="#C0C0C0",
                    highlightcolor="#A0A0A0",
                    insertbackground="black")
url_entry.pack(side="left", ipady=3)

# ==== Стиль кнопок ====
button_style = {
    "bg": "#E0E0E0",
    "fg": "black",
    "relief": "flat",
    "bd": 0,
    "overrelief": "flat",
    "activebackground": "#CDEAFF",
    "activeforeground": "black",
    "font": ("Segoe UI", 9),
    "padx": 10,
    "pady": 1,
    "height": 1,
    "takefocus": 0
}

def style_hover(btn):
    btn.bind("<Enter>", lambda e: btn.config(bg="#CDEAFF"))
    btn.bind("<Leave>", lambda e: btn.config(bg="#E0E0E0"))

# ==== Кнопки с тонкой рамкой ====
paste_frame = tk.Frame(entry_frame, bg="black", padx=0.5, pady=0.5)
paste_button = tk.Button(paste_frame, text="Paste", command=paste_link, **button_style)
paste_button.pack()
paste_frame.pack(side="left", padx=5)
style_hover(paste_button)

clear_frame = tk.Frame(entry_frame, bg="black", padx=0.5, pady=0.5)
clear_button = tk.Button(clear_frame, text="Clear", command=clear_input, **button_style)
clear_button.pack()
clear_frame.pack(side="left", padx=0)
style_hover(clear_button)

download_frame = tk.Frame(root, bg="black", padx=0.5, pady=0.5)
download_button = tk.Button(download_frame, text="Download", command=download_track, **button_style)
download_button.pack()
download_frame.pack(pady=15)
style_hover(download_button)

status_label = tk.Label(root, text="", fg="green", bg="#F5F5F5", font=("Segoe UI", 9))
status_label.pack()

# ==== Кликабельный путь ====
path_label = tk.Label(root, text=f"📁 Path: {download_path}", fg="blue", bg="#F5F5F5", font=("Segoe UI", 8), cursor="hand2")
path_label.pack()
path_label.bind("<Button-1>", open_folder)

progress_frame = tk.Frame(root, bg="#F5F5F5")
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, length=400)
progress_bar.pack()
progress_status_label = tk.Label(progress_frame, text="", bg="#F5F5F5", font=("Segoe UI", 9))
progress_status_label.pack()
progress_frame.pack_forget()

root.mainloop()