# LinuxOps Monitor – System Health Monitoring & Alerting Tool

A lightweight, production-sensible DevOps tool designed to monitor local system resources (CPU, Memory, Disk), analyze core OS log files for security and execution errors, and generate structured alert notifications. Developed to simulate an enterprise monitoring agent for L1 DevOps / SRE operations roles.

---

## 🔍 Features & Architecture

```mermaid
graph TD
    Cron[Cron Job / User Trigger] -->|Executes every 5m| RunAll[run_all.sh]
    RunAll -->|Invokes| Monitor[monitor.py]
    RunAll -->|Invokes| LogScan[log_scan.sh]
    
    subgraph "Resource Monitoring"
        Monitor -->|Reads| PSUtil[psutil API]
        Monitor -->|Checks status| Systemctl[systemctl services]
    end
    
    subgraph "Log Analysis"
        LogScan -->|Scans| Syslog[/var/log/syslog]
        LogScan -->|Scans| Authlog[/var/log/auth.log]
    end
    
    Monitor -->|Appends warning/critical alerts| Incidents[incidents.log]
    LogScan -->|Appends log anomalies| Incidents
    RunAll -->|Consolidates stdout report| Console[Terminal / Cron Output]
```

- **Resource Monitoring (`monitor.py`)**: Uses Python and `psutil` to track CPU, Memory, and Disk Usage against custom-configured thresholds (Warning/Critical levels) and inspects core services status.
- **Log Scanning (`log_scan.sh`)**: A Bash scanner searching `/var/log/syslog` and `/var/log/auth.log` for error signatures, service failure notifications, and authentication failures. It includes automated fallbacks to scan mock log files for development environments.
- **Unified Command Center (`run_all.sh`)**: Orchestrates both scripts, checks if new incidents have been generated during the current execution, and outputs a clean, unified status summary.
- **Incident Logging (`incidents.log`)**: Outputs to a centralized, greppable structured log format (`hostname | metric | severity | timestamp`) ideal for log forwarding tools like Fluentd, Logstash, or Datadog.
- **Operational Playbook (`RUNBOOK.md`)**: A complete incident-handling runbook, triage checklist, and shift-handover guide mapping directly to output alerts.

---

## 🚀 Setup & Installation

### 1. Prerequisites & Dependencies
Ensure Python 3 and Bash are installed on your Linux / WSL / EC2 environment.

```bash
# Update local package index
sudo apt update && sudo apt install -y python3 python3-pip git

# Install required Python modules
pip install psutil
```

### 2. Clone and Initialize Project
Create a folder structure and copy the files into place:

```bash
# Clone the repository (or initialize a new one)
git clone <your-repository-url>
cd linuxops-monitor

# Make shell scripts and python scripts executable
chmod +x run_all.sh log_scan.sh monitor.py
```

---

## 💻 Usage

### Manual Check
Run the unified script directly to check system status:
```bash
./run_all.sh
```

### Scheduling with Cron
To automate health checks to run every 5 minutes:
1. Open the crontab editor:
   ```bash
   crontab -e
   ```
2. Append the following line (make sure to use the absolute path to your script):
   ```cron
   */5 * * * * /path/to/linuxops-monitor/run_all.sh >> /path/to/linuxops-monitor/cron_execution.log 2>&1
   ```
3. To verify if cron is running:
   ```bash
   sudo systemctl status cron    # Ubuntu/Debian
   # Check cron execution logs:
   grep CRON /var/log/syslog
   ```

---

## 🧪 Simulation and Alert Testing
To test the alerting pipeline without overwhelming the system, you can feed simulated values or create mock logs.

### A. Testing CPU & Memory Alerts (Via Parameter Overrides)
Run `monitor.py` with custom, low thresholds that force immediate warnings or critical alerts:

```bash
# Trigger warnings for CPU (> 5%) and Memory (> 5%)
python3 monitor.py --cpu-warn 5 --cpu-crit 10 --mem-warn 5 --mem-crit 10
```

### B. Testing Log Scanner Alerts (Via Mock Logs)
If `/var/log/syslog` or `/var/log/auth.log` are empty, missing, or require root access, `log_scan.sh` will look for local mock files. Create mock logs in the project folder to simulate failures:

```bash
# Simulate a SSH Brute Force attack in mock auth log
echo "$(date "+%b %d %H:%M:%S") server sshd[1234]: Failed password for invalid user admin from 192.168.1.50 port 22 ssh2" > mock_auth.log

# Simulate a system service failure in mock syslog
echo "$(date "+%b %d %H:%M:%S") server systemd[1]: cron.service: Failed with result 'exit-code'." > mock_syslog.log
# Put multiple lines to cross the warning threshold (> 5 lines)
for i in {1..7}; do echo "$(date "+%b %d %H:%M:%S") server systemd[1]: systemd-hostnamed.service: Failed with exit-code." >> mock_syslog.log; done

# Execute scanner
./run_all.sh
```

Inspect the generated incidents:
```bash
cat incidents.log
```

---

## 📊 Sample Outputs

### Console Report
```text
========================================================================
      LINUXOPS MONITOR - MASTER HEALTH CHECK RUN
      Start Time: 2026-06-17 23:25:00
========================================================================
Executing system metrics health check...
============================================================
SYSTEM HEALTH STATUS REPORT - 2026-06-17 23:25:01
============================================================
Hostname:      prod-web-01
OS Platform:   linux
------------------------------------------------------------
CPU Usage:       4.5%   [Warn: >80.0%, Crit: >90.0%]
Memory Usage:   62.1%   [Warn: >85.0%, Crit: >95.0%]
Disk Usage:     35.2%   [Warn: >90.0%, Crit: >95.0%]
------------------------------------------------------------
Monitored Services Status:
  - ssh          : [RUNNING]
  - cron         : [RUNNING]
============================================================

Executing log file patterns scanner...
=========================================
LOG SCANNER REPORT - 2026-06-17 23:25:02
=========================================
Scanning Syslog (Simulated: /home/ubuntu/linuxops-monitor/mock_syslog.log)...
  - Total error/warning patterns found: 7
  - Most recent occurrences:
    * Jun 17 23:24:00 server systemd[1]: systemd-hostnamed.service: Failed with exit-code.
    * Jun 17 23:24:05 server systemd[1]: systemd-hostnamed.service: Failed with exit-code.
    * Jun 17 23:24:10 server systemd[1]: systemd-hostnamed.service: Failed with exit-code.
  [ALERT] Syslog error count exceeded threshold. Alert logged.
-
Scanning Auth Log (Simulated: /home/ubuntu/linuxops-monitor/mock_auth.log)...
  - Total authentication incidents/failures found: 1
  - Most recent occurrences:
    * Jun 17 23:20:00 server sshd[1234]: Failed password for invalid user admin from 192.168.1.50 port 22 ssh2
  [ALERT] Authentication failure(s) detected. Alert logged.
=========================================

========================================================================
      HEALTH CHECK COMPLETED AT 2026-06-17 23:25:02
      ALERT: 2 new incident(s) appended to incidents.log!
      --- Last 2 line(s) of incidents.log ---
      prod-web-01 | syslog_errors | WARNING | 2026-06-17 23:25:02
      prod-web-01 | auth_failures | CRITICAL | 2026-06-17 23:25:02
========================================================================
```

### incidents.log (Greppable Alert Log)
```text
prod-web-01 | syslog_errors | WARNING | 2026-06-17 23:25:02
prod-web-01 | auth_failures | CRITICAL | 2026-06-17 23:25:02
prod-web-01 | CPU | CRITICAL | 2026-06-17 23:30:04
```

---

## 🛠️ GitHub Repository Commands
To push this code to your own GitHub profile:

```bash
# Initialize git repository
git init

# Add all files to staging
git add README.md RUNBOOK.md monitor.py log_scan.sh run_all.sh

# Create initial commit
git commit -m "Initial commit: Core monitor scripts, log scanner, runbook and README"

# Link your remote repository and push (replace with your repository url)
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/linuxops-monitor.git
git push -u origin main
```
