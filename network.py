
import os
import json
import ipaddress
import subprocess

import psutil
import geoip2.database
import geoip2.errors


# ============================================================
# Configuration
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)

COUNTRY_DB_PATH = os.path.join(
    DATABASE_DIR,
    "GeoLite2-Country.mmdb"
)

ASN_DB_PATH = os.path.join(
    DATABASE_DIR,
    "GeoLite2-ASN.mmdb"
)

# Optional:
# Add GeoLite2-City.mmdb to the database folder
# if you want city information.
CITY_DB_PATH = os.path.join(
    DATABASE_DIR,
    "GeoLite2-City.mmdb"
)


# ============================================================
# IP INFORMATION
# ============================================================

def get_ip_details(ip_address):
    """
    Get IP information from local MaxMind databases.

    Country:
        GeoLite2-Country.mmdb

    City:
        GeoLite2-City.mmdb (optional)

    ASN:
        GeoLite2-ASN.mmdb

    Returns:
        country, city, asn, owner
    """

    country = "Unknown"
    city = "N/A"
    asn = "N/A"
    owner = "Unknown"

    # --------------------------------------------------------
    # Validate IP address
    # --------------------------------------------------------

    try:
        ip_obj = ipaddress.ip_address(ip_address)

    except ValueError:
        return (
            "Unknown",
            "N/A",
            "N/A",
            "Invalid IP"
        )

    # --------------------------------------------------------
    # Local / private IP
    # --------------------------------------------------------

    if (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
    ):
        return (
            "Local Network",
            "Internal",
            "N/A",
            "Private Range"
        )

    # ========================================================
    # COUNTRY DATABASE
    # ========================================================

    try:

        if os.path.isfile(COUNTRY_DB_PATH):

            with geoip2.database.Reader(
                COUNTRY_DB_PATH
            ) as reader:

                response = reader.country(
                    ip_address
                )

                if response.country.name:
                    country = response.country.name

        else:

            print(
                f"[COUNTRY] Database not found: "
                f"{COUNTRY_DB_PATH}"
            )

    except geoip2.errors.AddressNotFoundError:

        print(
            f"[COUNTRY] IP not found in database: "
            f"{ip_address}"
        )

    except Exception as error:

        print(
            f"[COUNTRY] Error for {ip_address}: "
            f"{error}"
        )

    # ========================================================
    # CITY DATABASE
    # ========================================================

    try:

        if os.path.isfile(CITY_DB_PATH):

            with geoip2.database.Reader(
                CITY_DB_PATH
            ) as reader:

                response = reader.city(
                    ip_address
                )

                if response.city.name:
                    city = response.city.name

                # If country database was unavailable,
                # use the country from the City database.

                if (
                    country == "Unknown"
                    and response.country.name
                ):
                    country = response.country.name

        else:

            # City database is optional.
            city = "N/A"

    except geoip2.errors.AddressNotFoundError:

        print(
            f"[CITY] IP not found in database: "
            f"{ip_address}"
        )

    except Exception as error:

        print(
            f"[CITY] Error for {ip_address}: "
            f"{error}"
        )

    # ========================================================
    # ASN DATABASE
    # ========================================================

    try:

        if os.path.isfile(ASN_DB_PATH):

            with geoip2.database.Reader(
                ASN_DB_PATH
            ) as reader:

                response = reader.asn(
                    ip_address
                )

                # --------------------------------------------
                # ASN Number
                # --------------------------------------------

                if (
                    response.autonomous_system_number
                    is not None
                ):

                    asn = (
                        "AS"
                        + str(
                            response
                            .autonomous_system_number
                        )
                    )

                # --------------------------------------------
                # ASN Organization
                # --------------------------------------------

                if (
                    response
                    .autonomous_system_organization
                ):

                    owner = (
                        response
                        .autonomous_system_organization
                    )

        else:

            print(
                f"[ASN] Database not found: "
                f"{ASN_DB_PATH}"
            )

    except geoip2.errors.AddressNotFoundError:

        print(
            f"[ASN] IP not found in database: "
            f"{ip_address}"
        )

    except Exception as error:

        print(
            f"[ASN] Error for {ip_address}: "
            f"{error}"
        )

    # ========================================================
    # Debug Information
    # ========================================================

    print(
        f"[IP INFO] "
        f"IP={ip_address} | "
        f"Country={country} | "
        f"City={city} | "
        f"ASN={asn} | "
        f"Owner={owner}"
    )

    # ========================================================
    # Return Result
    # ========================================================

    return (
        country,
        city,
        asn,
        owner
    )


# ============================================================
# NETWORK CONNECTIONS
# ============================================================

def get_network_connections():

    connections_list = []

    try:

        connections = psutil.net_connections(
            kind="inet"
        )

    except Exception as error:

        print(
            f"[NETWORK] Unable to retrieve "
            f"network connections: {error}"
        )

        return []

    for conn in connections:

        # ----------------------------------------------------
        # Get remote address
        # ----------------------------------------------------

        raddr = getattr(
            conn,
            "raddr",
            None
        )

        # ----------------------------------------------------
        # Only show established connections
        # ----------------------------------------------------

        if (
            conn.status != "ESTABLISHED"
            or not raddr
            or not getattr(raddr, "ip", None)
        ):
            continue

        remote_ip = raddr.ip
        remote_port = getattr(
            raddr,
            "port",
            0
        )

        pid = conn.pid

        # ----------------------------------------------------
        # Get process name
        # ----------------------------------------------------

        try:

            if pid:

                process = psutil.Process(pid)

                process_name = process.name()

            else:

                process_name = "System/Kernel"

        except psutil.NoSuchProcess:

            process_name = "Process Exited"

        except psutil.AccessDenied:

            process_name = "Access Denied"

        except Exception:

            process_name = "Unknown"

        # ----------------------------------------------------
        # Get IP information
        # ----------------------------------------------------

        (
            country,
            city,
            asn,
            owner
        ) = get_ip_details(
            remote_ip
        )

        # ----------------------------------------------------
        # Store connection
        # ----------------------------------------------------

        connections_list.append({

            "pid": (
                pid
                if pid
                else 0
            ),

            "name": process_name,

            "ip": remote_ip,

            "port": remote_port,

            "country": country,

            "city": city,

            "asn": asn,

            "owner": owner

        })

    return connections_list


# ============================================================
# LISTENING PORTS
# ============================================================

def get_listening_ports():

    listening = []

    try:

        connections = psutil.net_connections(
            kind="inet"
        )

    except Exception as error:

        print(
            f"[PORTS] Unable to retrieve "
            f"listening ports: {error}"
        )

        return []

    for conn in connections:

        if conn.status != "LISTEN":
            continue

        pid = conn.pid

        # ----------------------------------------------------
        # Get process name
        # ----------------------------------------------------

        try:

            if pid:

                process = psutil.Process(pid)

                process_name = process.name()

            else:

                process_name = "System"

        except psutil.NoSuchProcess:

            process_name = "Process Exited"

        except psutil.AccessDenied:

            process_name = "Access Denied"

        except Exception:

            process_name = "Unknown"

        # ----------------------------------------------------
        # Get local address
        # ----------------------------------------------------

        local_address = conn.laddr

        if local_address:

            port = local_address.port

        else:

            port = 0

        # ----------------------------------------------------
        # Determine protocol
        # ----------------------------------------------------

        if conn.type == 1:

            protocol = "TCP"

        else:

            protocol = "UDP"

        # ----------------------------------------------------
        # Store listening port
        # ----------------------------------------------------

        listening.append({

            "pid": (
                pid
                if pid
                else 0
            ),

            "name": process_name,

            "port": port,

            "protocol": protocol

        })

    return listening


# ============================================================
# DNS CACHE
# ============================================================

def get_dns_cache():

    command = (
        "Get-DnsClientCache "
        "| Select EntryName, Data "
        "| ConvertTo-Json"
    )

    try:

        result = subprocess.run(

            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command
            ],

            capture_output=True,

            text=True,

            shell=True,

            timeout=10

        )

        if not result.stdout.strip():

            return []

        data = json.loads(
            result.stdout
        )

        # PowerShell returns a dictionary
        # when there is only one result.

        if isinstance(data, dict):

            data = [data]

        return data

    except json.JSONDecodeError as error:

        print(
            f"[DNS] JSON parsing error: "
            f"{error}"
        )

        return []

    except subprocess.TimeoutExpired:

        print(
            "[DNS] PowerShell command timed out"
        )

        return []

    except Exception as error:

        print(
            f"[DNS] Error retrieving DNS cache: "
            f"{error}"
        )

        return []


# ============================================================
# ARP TABLE
# ============================================================

def get_arp_table():

    try:

        result = subprocess.run(

            ["arp", "-a"],

            capture_output=True,

            text=True,

            shell=True

        )

        lines = result.stdout.splitlines()

        entries = []

        for line in lines:

            parts = line.split()

            if (
                len(parts) >= 3
                and "." in parts[0]
            ):

                entries.append({

                    "ip": parts[0],

                    "mac": parts[1],

                    "type": (
                        parts[2]
                        if len(parts) > 2
                        else ""
                    )

                })

        return entries

    except Exception as error:

        print(
            f"[ARP] Error retrieving ARP table: "
            f"{error}"
        )

        return []


# ============================================================
# ROUTING TABLE
# ============================================================

def get_routing_table():

    try:

        result = subprocess.run(

            [
                "route",
                "print",
                "-4"
            ],

            capture_output=True,

            text=True,

            shell=True

        )

        lines = result.stdout.splitlines()

        routes = []

        capture = False

        for line in lines:

            # ------------------------------------------------
            # Find IPv4 route table
            # ------------------------------------------------

            if "Network Destination" in line:

                capture = True

                continue

            if not capture:
                continue

            if not line.strip():
                continue

            if line.startswith("="):
                continue

            parts = line.split()

            if len(parts) >= 5:

                routes.append({

                    "destination": parts[0],

                    "netmask": parts[1],

                    "gateway": parts[2],

                    "interface": parts[3],

                    "metric": parts[4]

                })

        return routes

    except Exception as error:

        print(
            f"[ROUTING] Error retrieving "
            f"routing table: {error}"
        )

        return []

