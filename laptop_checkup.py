#!/usr/bin/env python3
"""
LinuxOps Monitor - Laptop Health Checkup Diagnostics Tool
Performs a deep scan of the host laptop resources across 12 distinct checkup categories:
1. System/OS Details
2. Uptime & User Sessions
3. Power/Battery Diagnostics
4. CPU Diagnostics & Core Load
5. RAM & Swap Diagnostics
6. Storage Drives Allocation
7. Disk I/O Activity Metrics
8. Network Traffic Diagnostics
9. Network Adapter Interfaces & IPs
10. Open Port / Socket Audits
11. Overall Process Statistics
12. Top Resource-Consuming Processes
"""

import os
import sys
import time
import socket
import platform
import datetime
import psutil

# Terminal Color Codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def get_color_for_percent(pct):
    if pct < 70:
        return GREEN
    elif pct < 85:
        return YELLOW
    return RED

def make_progress_bar(pct, width=20):
    filled = int(round(width * pct / 100))
    # Using clean cross-platform ASCII characters to prevent encoding errors on Windows
    bar = "#" * filled + "-" * (width - filled)
    color = get_color_for_percent(pct)
    return f"{color}[{bar}] {pct:5.1f}%{RESET}"

def get_cpu_info():
    cpu_name = platform.processor() or "Unknown Processor"
    cores_physical = psutil.cpu_count(logical=False) or 0
    cores_logical = psutil.cpu_count(logical=True) or 0
    return cpu_name, cores_physical, cores_logical

def get_battery_info():
    if not hasattr(psutil, "sensors_battery"):
        return None
    battery = psutil.sensors_battery()
    return battery

def get_uptime():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime = datetime.timedelta(seconds=int(uptime_seconds))
    return str(uptime)

def format_bytes(bytes_num):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:3.1f} PB"

def get_top_processes(n=3):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            if info['pid'] != 0:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    top_cpu = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:n]
    top_mem = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:n]
    return top_cpu, top_mem

def main():
    print(f"{BOLD}{BLUE}========================================================================{RESET}")
    print(f"{BOLD}{CYAN}             LAPTOP DIAGNOSTICS: 12-POINT SYSTEM CHECKUP                {RESET}")
    print(f"{BOLD}{BLUE}========================================================================{RESET}")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ------------------------------------------------------------------------
    # 1. System/OS Details
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[1] SYSTEM & OPERATING SYSTEM DETAILS{RESET}")
    print(f"  OS Type:      {platform.system()} {platform.release()} (Architecture: {platform.machine()})")
    print(f"  OS Version:   {platform.version()}")
    print(f"  Hostname:     {socket.gethostname()}")
    print(f"  Python Path:  {sys.executable}")
    
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 2. Uptime & Active User Sessions
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[2] SYSTEM UPTIME & USER SESSIONS{RESET}")
    print(f"  Current Uptime: {get_uptime()}")
    try:
        users = psutil.users()
        if users:
            print("  Active User Sessions:")
            for user in users:
                login_time = datetime.datetime.fromtimestamp(user.started).strftime("%Y-%m-%d %H:%M")
                host_str = f" from {user.host}" if user.host else ""
                print(f"    * {BOLD}{user.name}{RESET} (Terminal: {user.terminal or 'console'}{host_str}, Active since: {login_time})")
        else:
            print("  Active User Sessions: None or system runlevel restricted.")
    except Exception as e:
        print(f"  Active User Sessions: Could not retrieve ({str(e)})")
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 3. Power/Battery Diagnostics
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[3] POWER & BATTERY DIAGNOSTICS{RESET}")
    battery = get_battery_info()
    if battery:
        plugged_str = "Plugged In (Charging/AC Power)" if battery.power_plugged else "Running on Battery"
        plugged_color = GREEN if battery.power_plugged else YELLOW
        time_left = "N/A"
        if not battery.power_plugged and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
            time_left = str(datetime.timedelta(seconds=battery.secsleft))
        print(f"  Source:     {plugged_color}{plugged_str}{RESET}")
        print(f"  Charge:     {make_progress_bar(battery.percent, 30)}")
        print(f"  Time Left:  {time_left}")
    else:
        print("  Power diagnostics not supported (Device lacks battery sensors or is a desktop/VM).")
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 4. CPU Diagnostics & Core Load
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[4] CPU CORES & ARCHITECTURE LOAD{RESET}")
    cpu_name, cores_phys, cores_log = get_cpu_info()
    cpu_usage_total = psutil.cpu_percent(interval=0.5)
    cpu_freq = psutil.cpu_freq()
    freq_str = f"{cpu_freq.current:.1f} MHz (Max: {cpu_freq.max:.1f} MHz)" if cpu_freq else "Unknown"
    
    print(f"  CPU Model:    {cpu_name}")
    print(f"  Core Count:   {cores_phys} Physical Cores, {cores_log} Logical Processors")
    print(f"  Frequency:    {freq_str}")
    print(f"  Overall Load: {make_progress_bar(cpu_usage_total, 30)}")
    
    core_percentages = psutil.cpu_percent(interval=0.1, percpu=True)
    cores_line = "  Usage/Core:   "
    for i, pct in enumerate(core_percentages):
        cores_line += f"C{i}:{pct:.0f}% "
        if (i + 1) % 8 == 0 and i != len(core_percentages) - 1:
            cores_line += "\n                "
    print(cores_line)
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 5. RAM & Swap Diagnostics
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[5] SYSTEM MEMORY (RAM) & SWAP/PAGEFILE LIMITS{RESET}")
    virtual_mem = psutil.virtual_memory()
    swap_mem = psutil.swap_memory()
    
    print(f"  Physical RAM: Total: {format_bytes(virtual_mem.total)} | Used: {format_bytes(virtual_mem.used)} | Free: {format_bytes(virtual_mem.available)}")
    print(f"  RAM Load:     {make_progress_bar(virtual_mem.percent, 30)}")
    print(f"  Swap Space:   Total: {format_bytes(swap_mem.total)} | Used: {format_bytes(swap_mem.used)} | Free: {format_bytes(swap_mem.free)}")
    print(f"  Swap Load:    {make_progress_bar(swap_mem.percent, 30)}")
    
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 6. Storage Drives Allocation
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[6] STORAGE DRIVE ALLOCATION & CAPACITY{RESET}")
    partitions = psutil.disk_partitions(all=False)
    for part in partitions:
        if 'cdrom' in part.opts or not part.device:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total_disk = format_bytes(usage.total)
            free_disk = format_bytes(usage.free)
            used_disk = format_bytes(usage.used)
            print(f"  Drive {BOLD}{part.device}{RESET} [{part.fstype}] -> {part.mountpoint}:")
            print(f"    Size:  {total_disk} Total | {used_disk} Used | {free_disk} Free")
            print(f"    Usage: {make_progress_bar(usage.percent, 30)}")
        except Exception:
            pass
            
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 7. Disk I/O Activity Metrics
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[7] DISK READ/WRITE I/O PERFORMANCE{RESET}")
    try:
        disk_io = psutil.disk_io_counters()
        if disk_io:
            print(f"  Read Operations:  {disk_io.read_count:,} reads (Total: {format_bytes(disk_io.read_bytes)})")
            print(f"  Write Operations: {disk_io.write_count:,} writes (Total: {format_bytes(disk_io.write_bytes)})")
            # Calculate time spent doing I/O if available (Windows/Linux)
            if hasattr(disk_io, 'read_time'):
                print(f"  Active I/O Time:  Read time: {disk_io.read_time / 1000:.1f}s | Write time: {disk_io.write_time / 1000:.1f}s")
        else:
            print("  No Disk I/O statistics available.")
    except Exception as e:
        print(f"  Disk I/O stats not readable ({str(e)})")
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 8. Network Traffic Diagnostics
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[8] NETWORK INTERFACE TRAFFIC BANDWIDTH{RESET}")
    try:
        net_io = psutil.net_io_counters()
        print(f"  Packets:      Sent: {net_io.packets_sent:,} packets | Received: {net_io.packets_recv:,} packets")
        print(f"  Data Volume:  Sent: {format_bytes(net_io.bytes_sent)} | Received: {format_bytes(net_io.bytes_recv)}")
        if net_io.dropin or net_io.dropout:
            print(f"  Packet Drops: Inward: {net_io.dropin} | Outward: {net_io.dropout}")
        if net_io.errin or net_io.errout:
            print(f"  Packet Errors: Inward: {net_io.errin} | Outward: {net_io.errout}")
    except Exception as e:
        print(f"  Network volume indicators unavailable ({str(e)})")
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 9. Network Adapter Interfaces & IPs
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[9] NETWORK ADAPTERS & IP CONFIGURATION{RESET}")
    try:
        if_addrs = psutil.net_if_addrs()
        if_stats = psutil.net_if_stats()
        active_adapters = 0
        
        for name, addrs in if_addrs.items():
            # Check if adapter is active/up
            status = "UP"
            speed = "Unknown"
            if name in if_stats:
                status = "UP" if if_stats[name].isup else "DOWN"
                speed = f"{if_stats[name].speed} Mbps" if if_stats[name].speed > 0 else "Unknown"
            
            # Find IPv4 addresses
            ips = []
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    ips.append(addr.address)
                    
            if ips:
                active_adapters += 1
                ip_str = ", ".join(ips)
                print(f"  Adapter: {BOLD}{name}{RESET} [{status} | Speed: {speed}]:")
                print(f"    IPv4 Address(es): {ip_str}")
                
        if active_adapters == 0:
            print("  No active/up network adapters with configured IP addresses found.")
    except Exception as e:
        print(f"  Could not read adapter specifications ({str(e)})")
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 10. Open Port / Socket Audits
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[10] LISTENING PORTS & SERVICES SECURITY AUDIT{RESET}")
    try:
        # Request TCP connections in LISTEN state
        conns = psutil.net_connections(kind='inet')
        listening_ports = []
        for conn in conns:
            if conn.status == 'LISTEN':
                port = conn.laddr.port
                ip = conn.laddr.ip
                pid_str = f"PID {conn.pid}" if conn.pid else "System"
                
                # Retrieve process name
                proc_name = "Unknown"
                if conn.pid:
                    try:
                        proc_name = psutil.Process(conn.pid).name()
                    except Exception:
                        pass
                listening_ports.append((port, ip, pid_str, proc_name))
                
        if listening_ports:
            # Sort by port number
            listening_ports.sort(key=lambda x: x[0])
            print(f"  Active local servers listening for inbound traffic:")
            print(f"    {BOLD}{'Port':<8} | {'IP Address':<18} | {'Owner':<12} | {'Service Name':<20}{RESET}")
            print(f"    {'-'*8} + {'-'*18} + {'-'*12} + {'-'*20}")
            for port, ip, owner, srv in listening_ports[:15]: # Show top 15 to keep screen clean
                print(f"    {port:<8} | {ip:<18} | {owner:<12} | {srv:<20}")
            if len(listening_ports) > 15:
                print(f"    ... and {len(listening_ports) - 15} more listening sockets.")
        else:
            print("  No active listening ports found.")
    except Exception as e:
        print(f"  Listening socket access restricted ({str(e)}). Run with elevated privileges.")
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 11. Overall Process Statistics
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[11] RUNNING PROCESSES STATISTICS SUMMARY{RESET}")
    try:
        pids = psutil.pids()
        total_processes = len(pids)
        total_threads = 0
        
        for pid in pids:
            try:
                p = psutil.Process(pid)
                total_threads += p.num_threads()
            except Exception:
                pass
                
        print(f"  Total Active Processes: {total_processes:,}")
        print(f"  Total Process Threads:   {total_threads:,}")
    except Exception as e:
        print(f"  Process counters lookup failed ({str(e)})")
        
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # ------------------------------------------------------------------------
    # 12. Top Resource-Consuming Processes
    # ------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}[12] PROCESS RESOURCE WATCH (TOP CONSUMERS){RESET}")
    top_cpu, top_mem = get_top_processes(n=3)
    
    print(f"  {BOLD}Top CPU Consumers:{RESET}")
    for p in top_cpu:
        print(f"    * PID {p['pid']:<6} | {p['name']:<25} | CPU Usage: {p['cpu_percent']:.1f}%")
        
    print(f"  {BOLD}Top Memory Consumers:{RESET}")
    for p in top_mem:
        mem_pct = p['memory_percent'] or 0.0
        approx_mb = (virtual_mem.total * (mem_pct / 100)) / (1024 * 1024)
        print(f"    * PID {p['pid']:<6} | {p['name']:<25} | RAM Usage: {mem_pct:.1f}% (~{approx_mb:.0f} MB)")
        
    print(f"{BOLD}{BLUE}========================================================================{RESET}")

if __name__ == "__main__":
    main()
