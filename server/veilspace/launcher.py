import argparse
import base64
import ctypes
import ipaddress
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import urllib.request

import uvicorn

from veilspace.config import Settings
from veilspace.database import initialize_database
from veilspace.main import create_app


def default_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "VeilSpaceData"
    return Path.cwd() / "storage"


def lan_addresses() -> list[str]:
    addresses: set[str] = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = ipaddress.ip_address(item[4][0])
            if not address.is_loopback and not address.is_link_local:
                addresses.add(str(address))
    except OSError:
        pass
    return sorted(addresses)


def public_address() -> str | None:
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=3) as response:
            address = ipaddress.ip_address(response.read(64).decode().strip())
            return str(address) if address.version == 4 and address.is_global else None
    except (OSError, ValueError):
        return None


def configure_firewall(port: int) -> str:
    if sys.platform != "win32":
        return "Firewall: configure inbound access on your server if needed."
    program = str(Path(sys.executable).resolve()).replace("'", "''")
    name = f"VeilSpace TCP {port}"
    command = (
        "$ErrorActionPreference='Stop'; "
        f"Get-NetFirewallRule -Name '{name}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule; "
        f"New-NetFirewallRule -Name '{name}' -DisplayName '{name}' "
        f"-Direction Inbound -Action Allow -Protocol TCP -LocalPort {port} "
        f"-Program '{program}' -Profile Any | Out-Null"
    )
    if not ctypes.windll.shell32.IsUserAnAdmin():
        encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
        command = (
            "$ErrorActionPreference='Stop'; "
            "try { $p = Start-Process -FilePath powershell.exe "
            f"-ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand','{encoded}') "
            "-Verb RunAs -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode } catch { exit 1 }"
        )
        print("Approve the Windows administrator prompt to configure inbound access.", flush=True)
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "Firewall: setup failed. Inbound access must be configured manually."
    return (
        f"Firewall: inbound TCP {port} allowed for this executable."
        if result.returncode == 0
        else "Firewall: setup failed. Inbound access must be configured manually."
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="VeilSpaceServer")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--data-dir", type=Path, default=default_data_dir())
    parser.add_argument("--no-firewall", action="store_true")
    parser.add_argument("--no-public-ip", action="store_true")
    parser.add_argument("--initialize-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    data_dir = args.data_dir.resolve()
    try:
        initialize_database(data_dir)
    except (OSError, sqlite3.Error) as error:
        print(f"Cannot initialize data: {error}", file=sys.stderr)
        return 1
    print(f"VeilSpace server\nData: {data_dir}", flush=True)
    if args.initialize_only:
        print("Database ready.", flush=True)
        return 0
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if os.name == "nt":
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        listener.bind((args.host, args.port))
        listener.listen(128)
    except OSError as error:
        listener.close()
        print(f"Cannot listen on port {args.port}: {error}", file=sys.stderr)
        return 1
    try:
        loopback_only = args.host in ("127.0.0.1", "localhost")
        if not args.no_firewall and not loopback_only:
            print(configure_firewall(args.port), flush=True)
        print(f"Local: http://127.0.0.1:{args.port}", flush=True)
        if not loopback_only:
            for address in lan_addresses():
                print(f"Network: http://{address}:{args.port}", flush=True)
            address = None if args.no_public_ip else public_address()
            if address:
                print(f"Public candidate: http://{address}:{args.port}", flush=True)
            print("External access depends on your provider firewall and routing.", flush=True)
        settings = Settings(environment="production", data_dir=data_dir)
        uvicorn.Server(uvicorn.Config(create_app(settings), log_level="info")).run(sockets=[listener])
    finally:
        listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
