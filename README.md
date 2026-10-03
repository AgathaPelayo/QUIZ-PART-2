# Mini Network Automation Project

## Purpose
This project automates a basic health check of Cisco network devices. Instead of
logging into each router, switch, or firewall one by one, `network_check.py` reads
a device inventory, checks every device, reports whether each one is **UP** or
**DOWN**, and saves the results to a JSON file for record-keeping.

## Project Structure
```
automation_project/
├── inventory.json      # List of Cisco devices to check
├── network_check.py    # Main automation script
├── README.md           # Documentation
└── output.json         # Results of the latest check (generated)
```

## Managed Devices
| Hostname     | IP Address    | Model               |
|--------------|---------------|---------------------|
| CORE-RTR-01  | 192.168.1.1   | Cisco ISR 4331      |
| DIST-SW-01   | 192.168.1.2   | Cisco Catalyst 3850 |
| ACCESS-SW-01 | 192.168.1.3   | Cisco Catalyst 2960 |
| EDGE-FW-01   | 192.168.1.254 | Cisco ASA 5506-X    |

## Requirements
- Python 3.8 or newer
- No third-party libraries (uses only the standard library)

## Usage
Run a simulated check (default, works without real equipment):
```bash
python network_check.py
```

Run a live check (attempts a TCP connection to each device's SSH port):
```bash
python network_check.py --mode live --timeout 3
```

Use custom input/output files:
```bash
python network_check.py --inventory my_devices.json --output report.json
```

## How Status Is Determined
- **Simulate mode:** uses each device's `simulated_status` field in `inventory.json`.
- **Live mode:** opens a TCP connection to the device's `port` (default 22).
  A successful connection, or a refused connection (host is alive but the port is
  closed), counts as **UP**. A timeout or unreachable host counts as **DOWN**.
- Devices with invalid data (missing hostname/IP, bad IP, bad port) are marked **ERROR**.

## Error Handling
- Missing or unreadable `inventory.json`
- Invalid JSON syntax or missing `devices` list
- Missing required fields, invalid IP addresses, invalid ports
- Connection timeouts and unreachable hosts
- Failure to write `output.json`
- Ctrl+C interruption

## Adding a Device
Add a new entry to the `devices` list in `inventory.json`:
```json
{
  "hostname": "ACCESS-SW-02",
  "ip": "192.168.1.4",
  "device_type": "cisco_ios",
  "model": "Cisco Catalyst 2960",
  "port": 22,
  "simulated_status": "UP"
}
```

## Sample Output
```
Network Device Status Check  (mode: simulate)
==============================================================================
HOSTNAME       IP ADDRESS       MODEL                 STATUS  DETAILS
------------------------------------------------------------------------------
CORE-RTR-01    192.168.1.1      Cisco ISR 4331        UP      Simulated check
DIST-SW-01     192.168.1.2      Cisco Catalyst 3850   UP      Simulated check
ACCESS-SW-01   192.168.1.3      Cisco Catalyst 2960   DOWN    Simulated check
EDGE-FW-01     192.168.1.254    Cisco ASA 5506-X      UP      Simulated check
------------------------------------------------------------------------------
Total: 4 | UP: 3 | DOWN: 1 | ERROR: 0
```
