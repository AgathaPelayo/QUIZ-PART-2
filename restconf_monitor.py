#!/usr/bin/env python3
"""
restconf_monitor.py - RESTCONF Network Monitoring Script

Connects to a Cisco IOS XE router over HTTPS using RESTCONF, retrieves
interface information from the ietf-interfaces YANG model, and displays
each interface's name and enabled status along with the HTTP status code.

Usage:
  python restconf_monitor.py
  python restconf_monitor.py --host <ip> --username <user> --password <pass> --port 443
"""

import argparse
import sys

import requests
import urllib3

# Lab routers use self-signed certificates, so certificate verification is
# turned off and the related warning is suppressed to keep output readable.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Router information from the lab instructions
ROUTER_IP = "192.168.10.1"
USERNAME = "admin"
PASSWORD = "Cisco123!"
RESOURCE = "/restconf/data/ietf-interfaces:interfaces"

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}


def get_interfaces(host, port, username, password, timeout):
    """Send a RESTCONF GET request and return the response (or None on failure)."""
    url = f"https://{host}:{port}{RESOURCE}"
    print(f"Connecting to router via HTTPS...")
    print(f"GET {url}\n")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            auth=(username, password),
            verify=False,
            timeout=timeout,
        )
        return response
    except requests.exceptions.ConnectTimeout:
        print(f"[ERROR] Connection timed out. The router at {host} did not respond "
              f"within {timeout} seconds.")
    except requests.exceptions.SSLError as e:
        print(f"[ERROR] SSL/HTTPS error while connecting to {host}: {e}")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Failed to connect to {host}. Check that the router is "
              f"reachable and that RESTCONF is enabled (ip http secure-server, restconf).")
    except requests.exceptions.Timeout:
        print(f"[ERROR] The request to {host} timed out while waiting for a response.")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
    return None


def display_interfaces(response):
    """Show the HTTP status code and each interface's name and enabled status."""
    print(f"HTTP Status Code: {response.status_code} ({response.reason})")

    if response.status_code == 401:
        print("[ERROR] Authentication failed. Check the username and password.")
        return False
    if response.status_code == 404:
        print("[ERROR] RESTCONF resource not found. Check the URL or that RESTCONF is enabled.")
        return False
    if response.status_code != 200:
        print(f"[ERROR] Unexpected response from router:\n{response.text}")
        return False

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] The router's response was not valid JSON.")
        return False

    interfaces = data.get("ietf-interfaces:interfaces", {}).get("interface", [])
    if not interfaces:
        print("No interfaces were returned by the router.")
        return True

    print()
    print(f"{'INTERFACE NAME':<30}{'ENABLED':<10}")
    print("-" * 40)
    for intf in interfaces:
        name = intf.get("name", "N/A")
        enabled = intf.get("enabled", "N/A")
        print(f"{name:<30}{str(enabled):<10}")
    print("-" * 40)
    enabled_count = sum(1 for i in interfaces if i.get("enabled") is True)
    print(f"Total interfaces: {len(interfaces)} | Enabled: {enabled_count} | "
          f"Disabled: {len(interfaces) - enabled_count}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Monitor Cisco IOS XE interfaces using RESTCONF.")
    parser.add_argument("--host", default=ROUTER_IP, help=f"Router IP (default: {ROUTER_IP})")
    parser.add_argument("--port", type=int, default=443, help="HTTPS port (default: 443)")
    parser.add_argument("--username", default=USERNAME, help="RESTCONF username")
    parser.add_argument("--password", default=PASSWORD, help="RESTCONF password")
    parser.add_argument("--timeout", type=float, default=10, help="Timeout in seconds (default: 10)")
    args = parser.parse_args()

    print("=" * 40)
    print(" RESTCONF Network Monitoring Script")
    print("=" * 40)

    response = get_interfaces(args.host, args.port, args.username, args.password, args.timeout)
    if response is None:
        print("\nMonitoring failed: could not retrieve interface information.")
        sys.exit(1)

    if not display_interfaces(response):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n[INFO] Monitoring cancelled by user.")
