# QUIZ-PART-2: Python Network Automation

A set of four Python network automation programs for managing and monitoring
Cisco devices: a device inventory tool, a RESTCONF monitoring script, a RESTCONF
interface configuration tool, and a mini network automation project.

## Group Members
- Agatha Fei R. Pelayo
- [Member name]
- [Member name]

## Repository Structure
```
QUIZ-PART-2/
├── network_inventory.py      # Task 1 - Python Network Inventory Tool
├── restconf_monitor.py       # Task 2 - RESTCONF Network Monitoring Script
├── interface_automation.py   # Task 3 - Automated Interface Configuration Tool
├── inventory.json            # Task 4 - Device inventory
├── network_check.py          # Task 4 - Device status checker
├── output.json               # Task 4 - Results of the latest check
└── README.md                 # Documentation
```

Each task was developed on its own branch (`task1`, `task2`, `task3`, `task4`)
and merged into `main`.

## Requirements
- Python 3.8 or newer
- `requests` library (Tasks 2 and 3 only):
  ```bash
  pip install requests
  ```
- Tasks 2 and 3 need a Cisco IOS XE router with RESTCONF enabled:
  ```
  ip http secure-server
  restconf
  ```

---

## Task 1: Python Network Inventory Tool
**File:** `network_inventory.py`

Stores Cisco devices in a Python list of dictionaries. Each device has a
hostname, management IP address, device type, location, and status.

**Features**
- Displays all devices in a table
- Displays only devices whose status is `up`
- Counts how many devices are operational

**Run**
```bash
python network_inventory.py
```

---

## Task 2: RESTCONF Network Monitoring Script
**File:** `restconf_monitor.py`

Connects to a Cisco IOS XE router over HTTPS and retrieves interface
information using RESTCONF.

| Setting  | Value |
|----------|-------|
| Router IP | 192.168.10.1 |
| Username | admin |
| Password | Cisco123! |
| Resource | `/restconf/data/ietf-interfaces:interfaces` |

**Features**
- Sends an HTTPS GET request with the `requests` library
- Displays the HTTP status code
- Displays each interface's name and enabled status
- Handles failed connections, timeouts, SSL errors, authentication errors (401),
  and missing resources (404)

**Run**
```bash
python restconf_monitor.py
```

To test against a different router (for example, a Cisco DevNet sandbox):
```bash
python restconf_monitor.py --host <ip> --port <port> --username <user> --password <pass>
```

---

## Task 3: Automated Interface Configuration Tool
**File:** `interface_automation.py`

Configures Loopback100 on a Cisco IOS XE router using RESTCONF, then retrieves
it to verify the configuration.

| Setting | Value |
|---------|-------|
| Interface | Loopback100 |
| Description | STUDENT-AUTOMATION |
| IP Address | 10.100.100.1 |
| Subnet Mask | 255.255.255.255 |
| Status | Enabled |

**How it works**
1. Builds a JSON payload using the `ietf-interfaces` and `ietf-ip` YANG models.
2. Sends it with **HTTP PUT** to
   `https://<router>/restconf/data/ietf-interfaces:interfaces/interface=Loopback100`.
   PUT creates the interface if it does not exist or replaces it if it does,
   so the script can be run more than once safely.
3. Reports success (`201 Created` or `204 No Content`) or failure.
4. Sends an **HTTP GET** to the same URL and compares each setting to the
   intended value, marking each one PASS or FAIL.

**Run**
```bash
python interface_automation.py
```

Alternate router:
```bash
python interface_automation.py --host <ip> --port <port> --username <user> --password <pass>
```

---

## Task 4: Mini Network Automation Project
**Files:** `inventory.json`, `network_check.py`, `output.json`

### Purpose
Automates a basic health check of Cisco network devices. Instead of logging into
each device one by one, `network_check.py` reads the device inventory, checks
every device, reports whether each one is **UP** or **DOWN**, and saves the
results to `output.json`.

### Managed Devices
| Hostname     | IP Address    | Model               |
|--------------|---------------|---------------------|
| CORE-RTR-01  | 192.168.1.1   | Cisco ISR 4331      |
| DIST-SW-01   | 192.168.1.2   | Cisco Catalyst 3850 |
| ACCESS-SW-01 | 192.168.1.3   | Cisco Catalyst 2960 |
| EDGE-FW-01   | 192.168.1.254 | Cisco ASA 5506-X    |

### Usage
Simulated check (default, works without real equipment):
```bash
python network_check.py
```

Live check (attempts a TCP connection to each device's SSH port):
```bash
python network_check.py --mode live --timeout 3
```

Custom input and output files:
```bash
python network_check.py --inventory my_devices.json --output report.json
```

### How Status Is Determined
- **Simulate mode:** uses each device's `simulated_status` field in `inventory.json`.
- **Live mode:** opens a TCP connection to the device's `port` (default 22).
  A successful or refused connection means the host is alive (**UP**).
  A timeout or unreachable host means **DOWN**.
- Devices with invalid data (missing hostname or IP, invalid IP, invalid port)
  are marked **ERROR**.

### Error Handling
- Missing or unreadable `inventory.json`
- Invalid JSON or missing `devices` list
- Missing fields, invalid IP addresses, invalid ports
- Connection timeouts and unreachable hosts
- Failure to write `output.json`
- Ctrl+C interruption

### Adding a Device
Add an entry to the `devices` list in `inventory.json`:
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

---

## Notes
- Tasks 2 and 3 disable SSL certificate verification because lab routers
  normally use self-signed certificates. Do not do this in production.
- If the router at 192.168.10.1 is not reachable, Tasks 2 and 3 display a
  connection error instead of crashing.
