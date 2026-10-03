#!/usr/bin/env python3
"""
network_check.py - Mini Network Automation Project

Reads Cisco device information from inventory.json, checks whether each
device is UP or DOWN, displays the results, and saves them to output.json.

Modes:
  simulate (default) - uses the "simulated_status" field in inventory.json,
                       so the program runs without real lab equipment.
  live               - attempts a real TCP connection to each device's
                       management port (default 22/SSH).

Usage:
  python network_check.py
  python network_check.py --mode live --timeout 3
  python network_check.py --inventory inventory.json --output output.json
"""

import argparse
import ipaddress
import json
import socket
import sys
from datetime import datetime

REQUIRED_FIELDS = ("hostname", "ip")
DEFAULT_PORT = 22


def load_inventory(path):
    """Read and validate the inventory file. Exits on fatal errors."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"[ERROR] Inventory file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"[ERROR] Invalid JSON in {path}: {e}")
    except OSError as e:
        sys.exit(f"[ERROR] Could not read {path}: {e}")

    devices = data.get("devices") if isinstance(data, dict) else None
    if not isinstance(devices, list) or not devices:
        sys.exit(f"[ERROR] {path} must contain a non-empty 'devices' list.")
    return devices


def validate_device(device):
    """Return an error message if the device entry is invalid, else None."""
    if not isinstance(device, dict):
        return "Device entry is not a JSON object"
    missing = [f for f in REQUIRED_FIELDS if not device.get(f)]
    if missing:
        return f"Missing required field(s): {', '.join(missing)}"
    try:
        ipaddress.ip_address(device["ip"])
    except ValueError:
        return f"Invalid IP address: {device['ip']}"
    port = device.get("port", DEFAULT_PORT)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        return f"Invalid port: {port}"
    return None


def check_live(ip, port, timeout):
    """Try a TCP connection to the device's management port."""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return "UP", f"TCP port {port} reachable"
    except socket.timeout:
        return "DOWN", f"Connection to port {port} timed out"
    except ConnectionRefusedError:
        # Host answered but port is closed -> device is alive
        return "UP", f"Host reachable, port {port} refused"
    except OSError as e:
        return "DOWN", f"Unreachable ({e.strerror or e})"


def check_simulated(device):
    """Use the simulated_status field from the inventory."""
    status = str(device.get("simulated_status", "DOWN")).upper()
    if status not in ("UP", "DOWN"):
        return "DOWN", f"Unknown simulated status '{status}', treated as DOWN"
    return status, "Simulated check"


def check_device(device, mode, timeout):
    """Check one device and return a result dictionary."""
    result = {
        "hostname": device.get("hostname", "UNKNOWN") if isinstance(device, dict) else "UNKNOWN",
        "ip": device.get("ip", "N/A") if isinstance(device, dict) else "N/A",
        "model": device.get("model", "N/A") if isinstance(device, dict) else "N/A",
        "status": "DOWN",
        "details": "",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }

    error = validate_device(device)
    if error:
        result["status"] = "ERROR"
        result["details"] = error
        return result

    try:
        if mode == "live":
            status, details = check_live(device["ip"], device.get("port", DEFAULT_PORT), timeout)
        else:
            status, details = check_simulated(device)
    except Exception as e:  # safety net so one device never crashes the run
        status, details = "ERROR", f"Unexpected error: {e}"

    result["status"] = status
    result["details"] = details
    return result


def display_results(results, mode):
    print(f"\nNetwork Device Status Check  (mode: {mode})")
    print("=" * 78)
    print(f"{'HOSTNAME':<15}{'IP ADDRESS':<17}{'MODEL':<22}{'STATUS':<8}DETAILS")
    print("-" * 78)
    for r in results:
        print(f"{r['hostname']:<15}{r['ip']:<17}{r['model']:<22}{r['status']:<8}{r['details']}")
    print("-" * 78)
    up = sum(r["status"] == "UP" for r in results)
    down = sum(r["status"] == "DOWN" for r in results)
    err = sum(r["status"] == "ERROR" for r in results)
    print(f"Total: {len(results)} | UP: {up} | DOWN: {down} | ERROR: {err}\n")


def save_results(results, path, mode):
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "summary": {
            "total": len(results),
            "up": sum(r["status"] == "UP" for r in results),
            "down": sum(r["status"] == "DOWN" for r in results),
            "error": sum(r["status"] == "ERROR" for r in results),
        },
        "results": results,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Results saved to {path}")
    except OSError as e:
        print(f"[ERROR] Could not write {path}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Check the status of Cisco network devices.")
    parser.add_argument("--inventory", default="inventory.json", help="Path to inventory file")
    parser.add_argument("--output", default="output.json", help="Path to output file")
    parser.add_argument("--mode", choices=["simulate", "live"], default="simulate",
                        help="simulate (default) or live TCP check")
    parser.add_argument("--timeout", type=float, default=2.0, help="Timeout in seconds (live mode)")
    args = parser.parse_args()

    devices = load_inventory(args.inventory)
    results = [check_device(d, args.mode, args.timeout) for d in devices]
    display_results(results, args.mode)
    save_results(results, args.output, args.mode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n[INFO] Check cancelled by user.")
