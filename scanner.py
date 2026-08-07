import psutil
import subprocess
import os
import winreg
import time
import json
import csv
from datetime import datetime

def run_powershell(cmd):
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, shell=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ""

# ---------- Process Functions ----------
def get_signature_status(file_path):
    if not file_path or not os.path.exists(file_path):
        return "Unknown"
    cmd = f'Get-AuthenticodeSignature "{file_path}" | Select-Object -ExpandProperty Status'
    try:
        result = subprocess.check_output(['powershell', '-Command', cmd],
                                         stderr=subprocess.STDOUT,
                                         shell=True, timeout=5)
        return result.decode('utf-8').strip()
    except Exception:
        return "N/A"

def get_active_processes():
    proc_data = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'ppid']):
        try:
            info = proc.info
            path = info['exe'] or "Unknown"
            status = get_signature_status(path)
            suspicious_keywords = ["AppData", "Temp", "Downloads", "Users"]
            if any(key in path for key in suspicious_keywords) and status != "Valid":
                status = "🚩 SUSPICIOUS (Untrusted Path)"
            proc_data.append({
                "pid": info['pid'],
                "name": info['name'],
                "path": path,
                "cmdline": ' '.join(info['cmdline']) if info['cmdline'] else '',
                "ppid": info['ppid'],
                "status": status
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return proc_data

def build_tree(pid, proc_dict, level, visited):
    if pid in visited:
        return f"{'  ' * level}|- [CYCLE] {proc_dict.get(pid, {}).get('name', '?')} (PID:{pid})"
    visited.add(pid)
    proc = proc_dict.get(pid, {})
    indent = "  " * level + "|- "
    line = f"{indent}{proc.get('name', '?')} (PID:{pid})"
    children = [p for p in proc_dict.values() if p['ppid'] == pid]
    for child in children:
        line += "\n" + build_tree(child['pid'], proc_dict, level + 1, visited)
    return line

def get_process_tree():
    processes = get_active_processes()
    proc_dict = {p['pid']: p for p in processes}
    trees = []
    visited = set()
    for pid, proc in proc_dict.items():
        ppid = proc['ppid']
        if ppid not in proc_dict or ppid == 0:
            if pid not in visited:
                tree_structure = build_tree(pid, proc_dict, 0, visited)
                trees.append(tree_structure)
    return trees

# ---------- Services ----------
def get_services():
    services = []
    for service in psutil.win_service_iter():
        try:
            name = service.name()
            display_name = service.display_name()
            binpath = service.binpath()
            state = service.status()
            try:
                description = service.description()
            except Exception:
                description = "N/A"
            services.append({
                "name": name,
                "display_name": display_name,
                "binary_path": binpath,
                "start_type": service.start_type(),
                "state": state,
                "description": description
            })
        except:
            continue
    return services

# ---------- Scheduled Tasks ----------
def get_scheduled_tasks():
    cmd = "Get-ScheduledTask | Where State -ne 'Disabled' | Select TaskName, TaskPath, State, Actions | ConvertTo-Json"
    output = run_powershell(cmd)
    try:
        tasks = json.loads(output)
        if isinstance(tasks, dict):
            tasks = [tasks]
        return tasks
    except:
        return []

# ---------- Kernel Drivers ----------
def get_drivers():
    try:
        result = subprocess.run(['driverquery', '/FO', 'CSV'], capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2: return []
        reader = csv.DictReader(lines)
        drivers = [row for row in reader]
        return drivers
    except:
        return []

# ---------- Persistence: Registry ----------
def get_registry_persistence():
    locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Userinit"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Shell"),
    ]
    findings = []
    for hive, key in locations:
        hive_name = "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
        try:
            with winreg.OpenKey(hive, key) as reg_key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(reg_key, i)
                        findings.append({"hive": hive_name, "key": key, "name": name, "value": value})
                        i += 1
                    except OSError: break
        except FileNotFoundError: continue
    return findings

# ---------- Persistence: Startup Folders ----------
def get_startup_folders():
    paths = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
    ]
    files = []
    for folder in paths:
        if os.path.exists(folder):
            for item in os.listdir(folder):
                full = os.path.join(folder, item)
                if os.path.isfile(full):
                    files.append(full)
    return files

# ---------- Persistence: WMI Event Subscriptions ----------
def get_wmi_persistence():
    cmd = r"Get-WmiObject -Namespace root\subscription -Class __EventFilter | Select Name, Query"
    output = run_powershell(cmd)
    filters = [line.strip() for line in output.split('\n') if 'Name' in line]
    return filters

# ---------- Persistence: Browser Extensions ----------
def get_browser_extensions():
    extensions = []
    chrome_pref = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Preferences")
    if os.path.exists(chrome_pref):
        try:
            with open(chrome_pref, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ext_data = data.get('extensions', {}).get('settings', {})
            for ext_id, settings in ext_data.items():
                if settings.get('state', 0) == 1:
                    name = settings.get('manifest', {}).get('name', 'Unknown')
                    extensions.append(f"Chrome: {name}")
        except: pass
    return extensions