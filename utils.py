import subprocess
import sys
import os
import importlib.util
import hashlib
import time
from datetime import datetime

def get_timestamp():
    """Returns a formatted timestamp for logging."""
    return datetime.now().strftime("%H:%M:%S")

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Required to find folders/databases bundled inside the EXE.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def initialize_system():
    """
    Checks for required dependencies and installs them if missing with live logs.
    """
    required_packages = {
        'psutil': 'psutil',
        'tabulate': 'tabulate',
        'geoip2': 'geoip2'
    }
    
    print("=" * 60)
    print(f"[*] {get_timestamp()} - INITIALIZING SENTINEL CORE SUBSYSTEMS...")
    print("=" * 60)
    
    for package, import_name in required_packages.items():
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            print(f"[!] {get_timestamp()} - CRITICAL COMPONENT MISSING: '{package}'")
            print(f"[*] {get_timestamp()} - INITIATING OVER-THE-AIR INSTALLATION...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"[+] {get_timestamp()} - {package.upper()} SUCCESSFULLY DEPLOYED.")
            except Exception as e:
                print(f"[-] {get_timestamp()} - DEPLOYMENT FAILED: {e}")
                sys.exit(1)
        else:
            print(f"[+] {get_timestamp()} - MODULE VERIFIED: {package:<15} [LINKED]")
            time.sleep(0.05)

    print(f"\n[*] {get_timestamp()} - ALL SUBSYSTEMS ONLINE. READY FOR INVESTIGATION.\n")

def clear_screen():
    """Clears the terminal window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def terminate_process(pid):
    """Safely terminates a process."""
    import psutil
    try:
        process = psutil.Process(int(pid))
        name = process.name()
        process.terminate()
        process.wait(timeout=3)
        return True, f"SUCCESS: {name} (PID: {pid}) was neutralized."
    except psutil.NoSuchProcess:
        return False, "TARGET ERROR: Process already terminated or invalid PID."
    except psutil.AccessDenied:
        return False, "PRIVILEGE ERROR: Access denied. Elevate to Administrator."
    except Exception as e:
        return False, f"UNEXPECTED ERROR: {str(e)}"

def delete_suspicious_file(file_path):
    """Deletes a file from the disk."""
    try:
        if not file_path or not os.path.exists(file_path):
            return False, "FILE ERROR: Target path no longer exists."
        os.remove(file_path)
        return True, f"WIPE SUCCESSFUL: {os.path.basename(file_path)} has been deleted."
    except PermissionError:
        return False, "LOCK ERROR: File is currently in use by another process."
    except Exception as e:
        return False, f"WIPE FAILED: {str(e)}"

def hash_file(file_path, algo='sha256'):
    """Calculates the cryptographic hash of a target file."""
    if not os.path.exists(file_path):
        return None
    h = hashlib.new(algo)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()