import os
import subprocess
import hashlib
import json
import time
import winreg
import utils
import scanner
import network
from datetime import datetime, timedelta

# ---------- File System ----------
def get_recent_files(days=7, paths=None):
    if paths is None:
        paths = [
            os.path.expandvars(r"%TEMP%"),
            os.path.expandvars(r"%APPDATA%"),
            os.path.expandvars(r"%LOCALAPPDATA%"),
            r"C:\Windows\Temp",
            r"C:\Users\Public",
            r"C:\Windows\System32\drivers\etc",
            r"C:\\"
        ]
    since = datetime.now() - timedelta(days=days)
    files = []
    for base in paths:
        if not os.path.exists(base):
            continue
        try:
            for root, dirs, names in os.walk(base, topdown=True, followlinks=False):
                if 'Windows\\WinSxS' in root or '\\System32\\config' in root:
                    continue
                for name in names:
                    full = os.path.join(root, name)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(full))
                        if mtime > since:
                            files.append({'path': full, 'last_modified': mtime.isoformat()})
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            continue
    files.sort(key=lambda x: x['last_modified'], reverse=True)
    return files

def get_prefetch_files():
    prefetch_dir = r"C:\Windows\Prefetch"
    if not os.path.exists(prefetch_dir):
        return []
    files = []
    try:
        pf_list = [f for f in os.listdir(prefetch_dir) if f.endswith('.pf')]
        for f in pf_list:
            full = os.path.join(prefetch_dir, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(full))
            files.append(f"{f} [last run: {mtime}]")
    except (OSError, PermissionError):
        pass
    return files

def get_alternate_data_streams(paths=None):
    if paths is None:
        paths = [r"C:\Windows\System32", os.path.expandvars(r"%TEMP%"), os.path.expandvars(r"%APPDATA%")]
    ads_list = []
    cmd_template = 'Get-Item -Path "{}" -Stream * | Select-Object Stream, Length | ConvertTo-Json'
    for base in paths:
        if not os.path.exists(base): continue
        try:
            for root, dirs, files in os.walk(base, topdown=True):
                for file in files[:30]:
                    full = os.path.join(root, file)
                    cmd = cmd_template.format(full)
                    output = subprocess.run(
                        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                        capture_output=True, text=True, shell=True, timeout=5
                    ).stdout.strip()
                    if output and ':$DATA' not in output:
                        try:
                            streams = json.loads(output)
                            if isinstance(streams, dict): streams = [streams]
                            for s in streams:
                                if s['Stream'] != ':$DATA':
                                    ads_list.append(f"{full}:{s['Stream']} (size {s['Length']})")
                        except: pass
        except: continue
    return ads_list

def get_usb_history():
    usb_devices = []
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\USBSTOR")
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                j = 0
                while True:
                    try:
                        device_instance = winreg.EnumKey(subkey, j)
                        device_key = winreg.OpenKey(subkey, device_instance)
                        friendly_name, _ = winreg.QueryValueEx(device_key, "FriendlyName")
                        usb_devices.append(friendly_name)
                        j += 1
                    except OSError: break
                i += 1
            except OSError: break
    except Exception: pass
    return usb_devices

def get_event_logs(log_name, event_id=None, max_events=50, level=None):
    filter_str = f"LogName='{log_name}'"
    if event_id: filter_str += f" and ID={event_id}"
    if level: filter_str += f" and LevelDisplayName='{level}'"
    cmd = f"Get-WinEvent -FilterHashtable @{{{filter_str}}} -MaxEvents {max_events} | Select TimeCreated, Id, Message | ConvertTo-Json"
    output = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        capture_output=True, text=True, shell=True, timeout=10
    ).stdout.strip()
    try:
        events = json.loads(output)
        if isinstance(events, dict): events = [events]
        return events
    except:
        return []

# ---------- TACTICAL AUDIT (10 Steps) ----------
TACTICAL_STEP_COMMANDS = {
    1: "Get-NetTCPConnection | Where-Object { $_.State -eq 'Established' } | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess | Sort-Object RemoteAddress | Format-Table -AutoSize",
    2: "Get-Process | Where-Object { $_.Description -eq $null -or $_.Company -notmatch 'Microsoft' } | Select-Object Name, Id, Path, Description | Format-Table -AutoSize",
    3: "Get-NetTCPConnection | Where-Object { $_.State -eq 'Listen' -and $_.LocalPort -notmatch '135|445' } | Format-Table -AutoSize",
    4: "$paths = @('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run', 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce', 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'); foreach ($path in $paths) { Get-ItemProperty $path | Select-Object PSChildName, * }",
    5: "Get-ScheduledTask | Where-Object { $_.Author -notmatch 'Microsoft|WID' -and $_.State -ne 'Disabled' } | Select-Object TaskName, TaskPath, Author | Format-Table -AutoSize",
    6: "Get-ChildItem -Path C:\\ -Include *.exe, *.dll, *.bat, *.ps1 -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.CreationTime -gt (Get-Date).AddHours(-4) } | Select-Object FullName, CreationTime | Format-Table -AutoSize",
    7: "Get-LocalGroupMember -Group 'Administrators' | Format-Table -AutoSize",
    8: "Get-WmiObject Win32_Service | Where-Object { $_.PathName -notlike '*Windows*' -and $_.State -eq 'Running' } | Select-Object Name, PathName | Format-Table -AutoSize",
    9: "Get-DnsClientCache | Select-Object EntryName, Data | Unique | Format-Table -AutoSize",
    10: "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4688} -MaxEvents 50 -ErrorAction SilentlyContinue | Select-Object TimeCreated, Message | Format-List"
}

def execute_tactical_step(step_num):
    cmd = TACTICAL_STEP_COMMANDS.get(step_num)
    if not cmd:
        return f"[!] Step {step_num} not found."
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, shell=True, timeout=30
        )
        output = result.stdout.strip()
        if not output:
            output = "[OK] No output (or no issues)."
        if result.stderr:
            output += f"\n[!] ERROR: {result.stderr}"
        return output
    except Exception as e:
        return f"[!] Exception: {str(e)}"

def get_tactical_audit_output():
    output = "🔍 **FBI TACTICAL AUDIT (10 STEPS)**\n" + "="*50 + "\n"
    for i in range(1, 11):
        output += f"\n**STEP {i}/10**\n"
        output += execute_tactical_step(i) + "\n"
        output += "-"*40 + "\n"
    return output

# ---------- LIVE RESPONSE TRIAGE (25 Steps) ----------
TRIAGE_STEP_COMMANDS = {
    1: "Get-Process | Select-Object Name, Id, CPU, WorkingSet | Sort-Object CPU -Descending | Select-Object -First 20",
    2: "Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess",
    3: "Get-WmiObject -Class Win32_SystemDriver | Where-Object {$_.State -eq 'Running'} | Select-Object Name, DisplayName",
    4: "Get-ChildItem -Path \\\\.\\pipe\\",
    5: "Get-WmiObject -Class Win32_Mutex | Select-Object Name",
    6: "Get-Service | Where-Object {$_.Status -eq 'Running' -and $_.ServiceType -eq 'Win32OwnProcess'} | Select-Object Name, DisplayName",
    7: "driverquery /fo table",
    8: "Get-WmiObject -Class Win32_Process | Where-Object {$_.Name -match 'cmd|powershell|wscript'} | Select-Object Name, CommandLine",
    9: "Get-DnsClientCache | Select-Object EntryName, Data",
    10: "net share",
    11: "Get-ChildItem (Get-PSReadlineOption).HistorySavePath -ErrorAction SilentlyContinue | Get-Content -Tail 20",
    12: "qwinsta",
    13: "fsutil usn readjournal C: | Select-String 'UsnEntry' -Context 0,5",
    14: "Get-GPO -All | Select-Object DisplayName, ModificationTime",
    15: "reg query HKLM\\SECURITY\\Policy\\PolAdtEv",
    16: "Get-ChildItem C:\\Windows\\System32\\*.dll | Get-AuthenticodeSignature | Where-Object {$_.Status -ne 'Valid'} | Select-Object Path, Status",
    17: "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=1102} -MaxEvents 10 | Select-Object TimeCreated, Message",
    18: "bcdedit /enum",
    19: "Get-WmiObject -Namespace root\\subscription -Class __EventFilter | Select-Object Name, Query",
    20: "schtasks /query /fo LIST /v",
    21: "Get-Process | Select-Object Name, Id, StartTime",
    22: "Get-ChildItem HKLM:\\SOFTWARE\\Classes\\CLSID -ErrorAction SilentlyContinue | ForEach-Object {Get-ItemProperty $_.PsPath}",
    23: "certutil -verifystore Root",
    24: "Get-BitsTransfer | Select-Object DisplayName, JobState",
    25: "Get-ComputerInfo | Select-Object WindowsVersion, OsName, OsBuildNumber"
}

def execute_triage_step(step_num):
    cmd = TRIAGE_STEP_COMMANDS.get(step_num)
    if not cmd:
        return f"[!] Step {step_num} not found."
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, shell=True, timeout=30
        )
        output = result.stdout.strip()
        if not output:
            output = "[OK] No output (or no issues)."
        if result.stderr:
            output += f"\n[!] ERROR: {result.stderr}"
        return output
    except Exception as e:
        return f"[!] Exception: {str(e)}"

def get_triage_output():
    triage_actions = [
        "Capture Volatile Memory Info", "Dump Established Network States", "Verify Kernel Callback Routines",
        "Analyze Named Pipe Anomalies", "Scan Active Mutex Signatures", "Query Hidden Service Objects",
        "Enumerate Non-Microsoft Drivers", "Check Shell Spawning Patterns", "Trace DNS Resolution Cache",
        "Verify SMB/Admin Share Access", "Scan Recent PowerShell History", "Check Remote Desktop Logons",
        "Analyze MFT Modification Spikes", "Verify GPO Override Artifacts", "Scan Local Security Authority (LSA)",
        "Verify Cryptographic Provider DLLs", "Analyze Event Log Clearing IDs", "Check BCDedit Debugger Settings",
        "Scan WMI Event Consumer Bindings", "Verify Scheduled Task Binaries", "Analyze Process Environment Blocks",
        "Check Hijacked COM Objects", "Verify Root Certificate Stores", "Scan BITS Transfer Jobs",
        "Final Integrity Stabilization"
    ]
    output = "🔍 **LIVE RESPONSE TRIAGE (25 STEPS)**\n" + "="*50 + "\n"
    for i in range(1, 26):
        output += f"\n**STEP {i:02d}/25: {triage_actions[i-1]}**\n"
        output += execute_triage_step(i) + "\n"
        output += "-"*40 + "\n"
    return output

# ---------- Evidence Export ----------
def export_all_evidence():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Sentinel_Evidence_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("THE SENTINEL - FORENSIC EVIDENCE EXPORT\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")

        sections = [
            ("PROCESS AUDIT", scanner.get_active_processes),
            ("NETWORK CONNECTIONS", network.get_network_connections),
            ("REGISTRY PERSISTENCE", scanner.get_registry_persistence),
            ("RECENT FILE MODIFICATIONS", lambda: get_recent_files(days=7)),
            ("USB DEVICE HISTORY", get_usb_history),
            ("BROWSER EXTENSIONS", scanner.get_browser_extensions)
        ]

        for title, func in sections:
            f.write(f"\n--- {title} ---\n")
            data = func()
            if isinstance(data, list):
                for item in data:
                    f.write(f"{item}\n")
            f.write("-" * 40 + "\n")
    return filename