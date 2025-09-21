#!/usr/bin/env python3
"""
Cleanup script for FlipDisk system
Kills any hanging processes and cleans up ZMQ resources
"""
import psutil
import sys
import os

def kill_flipdisk_processes():
    """Kill any running FlipDisk processes"""
    killed_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's a Python process running our scripts
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(script in cmdline for script in ['FlipDisk.py', 'app.py', 'start_flipdisk.py']):
                    print(f"Killing process {proc.info['pid']}: {cmdline}")
                    proc.kill()
                    killed_processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return killed_processes

def main():
    print("🧹 FlipDisk Cleanup Utility")
    print("=" * 30)
    
    # Kill processes
    killed = kill_flipdisk_processes()
    
    if killed:
        print(f"✅ Killed {len(killed)} processes: {killed}")
    else:
        print("ℹ️  No FlipDisk processes found running")
    
    print("🏁 Cleanup complete")
    print("\nYou can now safely start FlipDisk again with:")
    print("   python start_flipdisk.py")

if __name__ == "__main__":
    main()