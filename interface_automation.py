#!/usr/bin/env python3
"""
interface_automation.py - Automated Interface Configuration Tool

Uses RESTCONF to configure Loopback100 on a Cisco IOS XE router, reports
whether the configuration succeeded, then retrieves Loopback100 and verifies
that the router's configuration matches what was sent.

Usage:
  python interface_automation.py
  python interface_automation.py --host <ip> --username <user> --password <pass> --port 443
"""

import argparse
import json
import sys

import requests
import urllib3

# Lab routers use self-signed certificates.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Router information from the lab instructions
ROUTER_IP = "192.168.10.1"
USERNAME = "admin"
PASSWORD = "Cisco123!"

# Interface settings to apply
INTERFACE_NAME = "Loopback100"
DESCRIPTION = "STUDENT-AUTOMATION"
IP_ADDRESS = "10.100.100.1"
SUBNET_MASK = "255.255.255.255"
ENABLED = True

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}


def build_payload():
    """Create the JSON payload using the ietf-interfaces and ietf-ip YANG models."""
    return {
        "ietf-interfaces:interface": {
            "name": INTERFACE_NAME,
            "description": DESCRIPTION,
            "type": "iana-if-type:softwareLoopback",
            "enabled": ENABLED,
            "ietf-ip:ipv4": {
                "address": [
                    {"ip": IP_ADDRESS, "netmask": SUBNET_MASK}
                ]
            },
        }
    }


def build_url(host, port):
    """RESTCONF URL that points to the Loopback100 entry in ietf-interfaces."""
    return f"https://{host}:{port}/restconf/data/ietf-interfaces:interfaces/interface={INTERFACE_NAME}"


def send_request(method, url, auth, timeout, payload=None):
    """Send a RESTCONF request and handle connection errors. Returns the response or None."""
    try:
        return requests.request(
            method,
            url,
            headers=HEADERS,
            auth=auth,
            data=json.dumps(payload) if payload is not None else None,
            verify=False,
            timeout=timeout,
        )
    except requests.exceptions.ConnectTimeout:
        print(f"[ERROR] Connection timed out after {timeout} seconds.")
    except requests.exceptions.SSLError as e:
        print(f"[ERROR] SSL/HTTPS error: {e}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Failed to connect to the router. Check that it is reachable "
              "and that RESTCONF is enabled (ip http secure-server, restconf).")
    except requests.exceptions.Timeout:
        print("[ERROR] The router did not respond in time.")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
    return None


def configure_interface(url, auth, timeout):
    """Send the configuration with HTTP PUT (creates or replaces Loopback100)."""
    payload = build_payload()
    print("Step 1: Sending configuration")
    print(f"PUT {url}")
    print("Payload:")
    print(json.dumps(payload, indent=2))
    print()

    response = send_request("PUT", url, auth, timeout, payload)
    if response is None:
        print("Configuration FAILED: could not reach the router.\n")
        return False

    print(f"HTTP Status Code: {response.status_code} ({response.reason})")
    if response.status_code == 201:
        print(f"Configuration SUCCEEDED: {INTERFACE_NAME} was created.\n")
        return True
    if response.status_code == 204:
        print(f"Configuration SUCCEEDED: {INTERFACE_NAME} was updated.\n")
        return True
    if response.status_code == 401:
        print("Configuration FAILED: authentication error. Check the username and password.\n")
    else:
        print(f"Configuration FAILED. Router response:\n{response.text}\n")
    return False


def verify_interface(url, auth, timeout):
    """Retrieve Loopback100 with HTTP GET and compare it to the intended settings."""
    print("Step 2: Verifying configuration")
    print(f"GET {url}")

    response = send_request("GET", url, auth, timeout)
    if response is None:
        print("Verification FAILED: could not reach the router.")
        return False

    print(f"HTTP Status Code: {response.status_code} ({response.reason})")
    if response.status_code == 404:
        print(f"Verification FAILED: {INTERFACE_NAME} does not exist on the router.")
        return False
    if response.status_code != 200:
        print(f"Verification FAILED. Router response:\n{response.text}")
        return False

    try:
        intf = response.json().get("ietf-interfaces:interface", {})
    except ValueError:
        print("Verification FAILED: the router's response was not valid JSON.")
        return False

    addresses = intf.get("ietf-ip:ipv4", {}).get("address", [{}])
    first = addresses[0] if addresses else {}

    checks = [
        ("Interface", INTERFACE_NAME, intf.get("name")),
        ("Description", DESCRIPTION, intf.get("description")),
        ("IP Address", IP_ADDRESS, first.get("ip")),
        ("Subnet Mask", SUBNET_MASK, first.get("netmask")),
        ("Enabled", ENABLED, intf.get("enabled")),
    ]

    print()
    print(f"{'SETTING':<14}{'EXPECTED':<22}{'ACTUAL':<22}RESULT")
    print("-" * 66)
    all_ok = True
    for label, expected, actual in checks:
        ok = expected == actual
        all_ok = all_ok and ok
        print(f"{label:<14}{str(expected):<22}{str(actual):<22}{'PASS' if ok else 'FAIL'}")
    print("-" * 66)

    if all_ok:
        print(f"Verification PASSED: {INTERFACE_NAME} is configured correctly.")
    else:
        print(f"Verification FAILED: {INTERFACE_NAME} does not match the intended configuration.")
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Configure Loopback100 on Cisco IOS XE using RESTCONF.")
    parser.add_argument("--host", default=ROUTER_IP, help=f"Router IP (default: {ROUTER_IP})")
    parser.add_argument("--port", type=int, default=443, help="HTTPS port (default: 443)")
    parser.add_argument("--username", default=USERNAME, help="RESTCONF username")
    parser.add_argument("--password", default=PASSWORD, help="RESTCONF password")
    parser.add_argument("--timeout", type=float, default=10, help="Timeout in seconds (default: 10)")
    args = parser.parse_args()

    print("=" * 66)
    print(" Automated Interface Configuration Tool (RESTCONF)")
    print("=" * 66)

    url = build_url(args.host, args.port)
    auth = (args.username, args.password)

    if not configure_interface(url, auth, args.timeout):
        sys.exit(1)
    if not verify_interface(url, auth, args.timeout):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n[INFO] Configuration cancelled by user.")
