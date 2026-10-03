#!/usr/bin/env python3

from typing import List, Dict


def get_devices() -> List[Dict[str, str]]:
    return [
        {
            "Hostname": "R1-core",
            "Management IP": "10.0.0.1",
            "Device Type": "Router",
            "Location": "Datacenter-1",
            "Status": "up",
        },
        {
            "Hostname": "SW1-access",
            "Management IP": "10.0.1.10",
            "Device Type": "Switch",
            "Location": "Floor-1",
            "Status": "down",
        },
        {
            "Hostname": "FW1-edge",
            "Management IP": "10.0.254.1",
            "Device Type": "Firewall",
            "Location": "Datacenter-1",
            "Status": "up",
        },
    ]


def display_devices(devices: List[Dict[str, str]]) -> None:
    if not devices:
        print("No devices to display.")
        return

    cols = ["Hostname", "Management IP", "Device Type", "Location", "Status"]
    widths = {c: len(c) for c in cols}
    for d in devices:
        for c in cols:
            widths[c] = max(widths[c], len(str(d.get(c, ""))))

    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    print(header)
    print(sep)
    for d in devices:
        print(" | ".join(str(d.get(c, "")).ljust(widths[c]) for c in cols))


def devices_with_status(devices: List[Dict[str, str]], status: str) -> List[Dict[str, str]]:
    s = status.lower()
    return [d for d in devices if str(d.get("Status", "")).lower() == s]


def count_operational(devices: List[Dict[str, str]]) -> int:
    return len(devices_with_status(devices, "up"))


def main() -> None:
    devices = get_devices()

    print("Network Inventory")
    print("=================\n")

    print("All devices:")
    display_devices(devices)
    print()

    up = devices_with_status(devices, "up")
    print("Devices with status 'up':")
    display_devices(up)
    print()

    print(f"Number of operational devices: {count_operational(devices)}")


if __name__ == "__main__":
    main()
