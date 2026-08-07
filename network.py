import psutil
import geoip2.database
import os
import subprocess
import json
import time
import utils

# Paths to GeoIP Databases (Create a folder named 'database' and place .mmdb files)
CITY_DB_PATH = utils.get_resource_path(os.path.join("database", "GeoLite2-City.mmdb"))
ASN_DB_PATH = utils.get_resource_path(os.path.join("database", "GeoLite2-ASN.mmdb"))

def get_ip_details(ip_address):
    """Provides Geo-IP and ISP data for a given IP."""
    if ip_address in ("127.0.0.1", "::1") or ip_address.startswith(("192.168.", "10.", "172.16.")):
        return "Local Network", "Internal", "Private Range"
    
    country, city, owner = "Unknown", "Unknown", "Unknown"
    try:
        if os.path.exists(CITY_DB_PATH):
            with geoip2.database.Reader(CITY_DB_PATH) as reader:
                response = reader.city(ip_address)
                country = response.country.name if response.country.name else "Unknown"
                city = response.city.name if response.city.name else "N/A"
        if os.path.exists(ASN_DB_PATH):
            with geoip2.database.Reader(ASN_DB_PATH) as asn_reader:
                asn_response = asn_reader.asn(ip_address)
                owner = asn_response.autonomous_system_organization if asn_response.autonomous_system_organization else "Unknown"
    except Exception:
        pass
    return country, city, owner

def get_network_connections():
    """Fetches established connections."""
    connections_list = []
    for conn in psutil.net_connections(kind='inet'):
        raddr = getattr(conn, 'raddr', None)
        if conn.status == 'ESTABLISHED' and raddr and raddr.ip:
            remote_ip = raddr.ip
            pid = conn.pid
            try:
                if pid:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                else:
                    proc_name = "System/Kernel"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = "Hidden/Unknown"

            country, city, owner = get_ip_details(remote_ip)
            connections_list.append({
                "pid": pid if pid else 0,
                "name": proc_name,
                "ip": remote_ip,
                "country": country,
                "city": city,
                "owner": owner
            })
    return connections_list

def get_listening_ports():
    listening = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'LISTEN':
            pid = conn.pid
            try:
                if pid:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                else:
                    proc_name = "System"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = "Unknown"
            
            laddr = conn.laddr
            port = laddr.port if laddr else 0
            protocol = 'TCP' if conn.type == 1 else 'UDP'
            listening.append({
                "pid": pid if pid else 0,
                "name": proc_name,
                "port": port,
                "protocol": protocol
            })
    return listening

def get_dns_cache():
    cmd = "Get-DnsClientCache | Select EntryName, Data | ConvertTo-Json"
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, shell=True, timeout=10
        )
        if not result.stdout:
            return []
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        return data
    except Exception:
        return []

def get_arp_table():
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, shell=True)
        lines = result.stdout.split('\n')
        entries = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 3 and '.' in parts[0]:
                entries.append({'ip': parts[0], 'mac': parts[1], 'type': parts[2] if len(parts) > 2 else ''})
        return entries
    except:
        return []

def get_routing_table():
    try:
        result = subprocess.run(['route', 'print', '-4'], capture_output=True, text=True, shell=True)
        lines = result.stdout.split('\n')
        routes = []
        capture = False
        for line in lines:
            if 'Network Destination' in line:
                capture = True
                continue
            if capture and line.strip() and not line.startswith('='):
                parts = line.split()
                if len(parts) >= 5:
                    routes.append({
                        'destination': parts[0],
                        'netmask': parts[1],
                        'gateway': parts[2],
                        'interface': parts[3],
                        'metric': parts[4] if len(parts) > 4 else ''
                    })
        return routes
    except:
        return []