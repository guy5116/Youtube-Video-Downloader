from yt_dlp import YoutubeDL
from pathlib import Path
import customtkinter as ctk
import queue, threading, time, sys, shutil
from dataclasses import dataclass

@dataclass
class VIDEO:
    url: str
    opt : dict

@dataclass
class VIDEO_QUEUE:
    current: int
    end: int

def main():
    download_button.configure(state="disabled")
    quality = None
    match quality_var.get().lower():
        case "worst":
            quality = "wv*[ext=mp4]+wa[ext=m4a]/w"
        case "best":
            quality = "bv*[ext=mp4]+ba[ext=m4a]/b"
        case "480":
            quality = "bv*[height<=480][ext=mp4]+ba[ext=m4a]/b"
        case "720":
            quality = "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b"
        case "1080":
            quality = "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b"
    url = video_url_entry.get()

    if url == "":
        console_output_textbox.insert('end', "URL Empty\n")
        download_button.configure(state="normal")
        return

    video_url_entry.delete(0, len(url))
    vid_queue.end += 1
    update_queue()
    download_button.configure(state="normal")

    if video_switch_var.get():
        output = BASE_DIR / "video_outputs"
        output.mkdir(exist_ok=True)

        ydl_opts = {
            "progress_hooks": [ytdlp_hook],
            "format": quality,
            "merge_output_format": "mp4",
            "outtmpl": str(output / "%(title)s.%(ext)s"),
            "cookiefile": str(BASE_DIR / "cookies.txt"),
            "js_runtimes": {
                "node":{
                    'path' : node_path
                }
            },
            "remote_components": ["ejs:github"]
        }

    else:
        output = BASE_DIR / "audio_outputs"
        output.mkdir(exist_ok=True)

        ydl_opts = {
            "progress_hooks": [ytdlp_hook],
            "format": "bestaudio/best",
            "outtmpl": str(output / "%(title)s.%(ext)s"),
            "cookiefile": str(BASE_DIR / "cookies.txt"),
            "js_runtimes": {
                "node":{
                    'path' : node_path
                }
            },
            "remote_components": ["ejs:github"],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    video = VIDEO(url, ydl_opts)
    videos.put(video)

def video_downloader():
    global downloader
    while running:
        while not videos.empty():
            video = videos.get()
            url = video.url
            ydl = video.opt
            try:
                with YoutubeDL(ydl) as ydl:
                    ydl.download([url])
                    log_queue.put("File Downloaded\n")
            except Exception as e:
                log_queue.put(f"Error Reading URL\nError: {e}")
                update_queue()
            vid_queue.current += 1
        time.sleep(0.1)

def update_queue():
    queue_var.set(f"{vid_queue.current}/{vid_queue.end}")

def ytdlp_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        log_queue.put(f"Downloading {percent} | {speed} | ETA {eta}")

    elif d["status"] == "finished":
        filepath = Path(d["filename"])
        output_dir = filepath.parent

        log_queue.put("Download finished")
        log_queue.put(f"Saved to: {output_dir}")
        log_queue.put(f"Processing may take a few seconds")


def process_queue():
    while not log_queue.empty():
        console_output_textbox.insert("end", log_queue.get() + "\n")
        console_output_textbox.see("end")
    app.after(100, process_queue)

def start_downloader():
    #console_output_textbox.delete("1.0", "end")
    console_output_textbox.insert('end',"Preparing Download may take a few seconds...\n")
    threading.Thread(target=main).start()

def switch_event():
    vid_aud = video_switch_var.get()
    if not vid_aud:
        quality_segmentedbutton.configure(state="disabled")
    else:
        quality_segmentedbutton.configure(state="normal")

def end_app():
    global downloader
    global running
    running = False
    while downloader.is_alive():
        time.sleep(0.1)
    app.destroy()

vid_queue = VIDEO_QUEUE(0,0)
videos = queue.Queue()
downloading = False

app = ctk.CTk()
app.geometry('400x485')
app.grid_columnconfigure(0,weight=1)
app.title("Youtube Video Downloader")

running = True
queue_var= ctk.StringVar(value="{vid_queue.current}/{vid_queue.end}")

downloader = threading.Thread(target=video_downloader)
downloader.start()


center_frame = ctk.CTkFrame(app)
center_frame.grid(column=0, row=0)

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent
log_queue = queue.Queue()

node_path = shutil.which("node")

if not node_path:
    log_queue.put("Node.js not found on PATH")
else:
    log_queue.put(f"Using Node.js at: {node_path}")


video_url_entry = ctk.CTkEntry(center_frame, placeholder_text="Enter Video URL", width=400)
video_url_entry.grid(row=0, column=1)

video_switch_var = ctk.BooleanVar(master=app, value=False)
video_switch = ctk.CTkSwitch(center_frame, text="Audio or Video", variable=video_switch_var, width=400, command=switch_event)
video_switch.grid(row=1, column=1)

quality_var = ctk.StringVar(value='Best')
quality_segmentedbutton = ctk.CTkSegmentedButton(center_frame,values=['Worst','480', '720', '1080','Best'], variable=quality_var)
quality_segmentedbutton.grid(row=2, column=1)

queue_label = ctk.CTkLabel(center_frame, textvariable=queue_var)
queue_label.grid(row=3, column=1)

download_button = ctk.CTkButton(center_frame, text="Download", command=start_downloader, width=400)
download_button.grid(row=4, column=1)

console_output_textbox = ctk.CTkTextbox(center_frame, width=400, height=290)
console_output_textbox.grid(row=5, column=1)

close_button = ctk.CTkButton(center_frame,text="Close", command=end_app, width=400)
close_button.grid(row=6, column=1)

credit_label = ctk.CTkLabel(center_frame, text="Educational Purposes Only :)\n-guy5116")
credit_label.grid(row=7, column=1)

app.after(0, update_queue)
process_queue()
switch_event()
app.mainloop()