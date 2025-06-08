#!/usr/bin/env python3
"""
Force Auto-Accept Bluetooth Speaker
This version aggressively auto-accepts ALL pairing requests using multiple strategies
"""

import subprocess
import time
import signal
import sys
import threading
import os
import pexpect

class ForceAutoAcceptBluetoothSpeaker:
    def __init__(self):
        self.device_name = "Ubuntu-Speaker"
        self.running = True
        self.bluetoothctl_process = None
        
    def log(self, message):
        """Simple logging with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def run_command(self, command, timeout=10):
        """Run shell command with timeout"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def clear_old_pairings(self):
        """Remove any existing problematic pairings"""
        self.log("🧹 Clearing old pairings...")
        
        success, output, _ = self.run_command("bluetoothctl paired-devices")
        if success and output.strip():
            for line in output.strip().split('\n'):
                if line.strip() and 'Device' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        mac = parts[1]
                        self.log(f"Removing old pairing: {mac}")
                        self.run_command(f"echo 'remove {mac}' | bluetoothctl")
    
    def setup_bluetooth_aggressive(self):
        """Set up Bluetooth with multiple auto-accept strategies"""
        self.log("🔧 Setting up aggressive auto-accept Bluetooth...")
        
        # Kill any existing bluetoothd processes
        self.run_command("sudo pkill bluetoothd")
        time.sleep(2)
        
        # Restart Bluetooth service
        self.run_command("sudo systemctl restart bluetooth")
        time.sleep(3)
        
        # Configure bluetoothctl with multiple agent types
        bt_setup_commands = [
            "power on",
            "agent off",  # Turn off any existing agent
            "agent NoInputNoOutput",  # Try NoInputNoOutput first
            "default-agent",
            "discoverable on",
            "pairable on",
            f"system-alias {self.device_name}",
        ]
        
        for cmd in bt_setup_commands:
            success, output, error = self.run_command(f"echo '{cmd}' | bluetoothctl")
            self.log(f"Command '{cmd}': {'✅' if success else '❌'}")
            time.sleep(1)
        
        return True
    
    def start_aggressive_pairing_agent(self):
        """Start an aggressive pairing agent that handles all scenarios"""
        self.log("🤖 Starting aggressive pairing agent...")
        
        def pairing_agent_worker():
            """Worker thread for handling pairing requests"""
            try:
                # Start bluetoothctl with pexpect for real-time interaction
                child = pexpect.spawn('bluetoothctl', timeout=None)
                child.logfile_read = sys.stdout.buffer
                
                # Set up agent
                child.sendline('agent NoInputNoOutput')
                child.expect(['Agent registered', pexpect.TIMEOUT], timeout=5)
                
                child.sendline('default-agent')
                child.expect(['Default agent request successful', pexpect.TIMEOUT], timeout=5)
                
                self.log("🤖 Aggressive pairing agent ready - will auto-accept EVERYTHING!")
                
                while self.running:
                    try:
                        # Look for any pairing-related prompts
                        index = child.expect([
                            r'.*[Cc]onfirm.*',
                            r'.*[Pp]asskey.*',
                            r'.*[Pp]in.*',
                            r'.*[Aa]uthorize.*',
                            r'.*[Aa]ccept.*',
                            r'.*\[yes/no\].*',
                            r'.*\(yes/no\).*',
                            r'.*Request.*',
                            pexpect.TIMEOUT
                        ], timeout=10)
                        
                        if index < 8:  # Any pairing prompt
                            self.log("🔓 AUTO-ACCEPTING pairing request!")
                            child.sendline('yes')
                            time.sleep(1)
                        else:  # Timeout
                            continue
                            
                    except pexpect.EOF:
                        self.log("⚠️  Bluetoothctl connection lost, restarting...")
                        break
                    except Exception as e:
                        if self.running:
                            self.log(f"⚠️  Agent error: {e}, continuing...")
                        time.sleep(1)
                        
            except Exception as e:
                self.log(f"❌ Pairing agent failed: {e}")
            finally:
                try:
                    child.close()
                except:
                    pass
        
        # Start the pairing agent in a background thread
        agent_thread = threading.Thread(target=pairing_agent_worker, daemon=True)
        agent_thread.start()
        
        return True
    
    def start_dbus_auto_accept(self):
        """Start D-Bus monitoring for pairing requests"""
        self.log("🔌 Starting D-Bus auto-accept monitor...")
        
        def dbus_worker():
            """Monitor D-Bus for Bluetooth pairing events"""
            try:
                # Create a script to monitor D-Bus events
                dbus_script = '''
import subprocess
import sys
import time

def auto_accept_pairing():
    """Auto-accept any pairing request via D-Bus"""
    try:
        # Monitor for pairing requests
        while True:
            # Check for any pending authorization requests
            result = subprocess.run(['bluetoothctl', 'devices'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Auto-trust any connected devices
                for line in result.stdout.split('\\n'):
                    if 'Device' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            mac = parts[1]
                            # Trust the device
                            subprocess.run(['bluetoothctl', 'trust', mac], 
                                         capture_output=True)
            
            time.sleep(2)
            
    except Exception as e:
        print(f"D-Bus worker error: {e}")

if __name__ == "__main__":
    auto_accept_pairing()
'''
                
                # Write and execute the D-Bus script
                with open('/tmp/dbus_auto_accept.py', 'w') as f:
                    f.write(dbus_script)
                
                subprocess.run([sys.executable, '/tmp/dbus_auto_accept.py'])
                
            except Exception as e:
                if self.running:
                    self.log(f"D-Bus worker error: {e}")
        
        # Start D-Bus worker in background
        dbus_thread = threading.Thread(target=dbus_worker, daemon=True)
        dbus_thread.start()
        
        return True
    
    def monitor_and_auto_trust(self):
        """Monitor connections and auto-trust devices"""
        self.log("👁️  Starting connection monitor with auto-trust...")
        
        last_devices = set()
        
        while self.running:
            try:
                # Get all devices (paired and unpaired)
                success, output, _ = self.run_command("bluetoothctl devices")
                
                if success and output.strip():
                    current_devices = set()
                    for line in output.strip().split('\n'):
                        if line.strip() and 'Device' in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                mac = parts[1]
                                current_devices.add(mac)
                                
                                # Auto-trust any device we see
                                self.run_command(f"echo 'trust {mac}' | bluetoothctl")
                                
                                # Check if it's connected
                                conn_success, conn_output, _ = self.run_command(f"bluetoothctl info {mac}")
                                if conn_success and "Connected: yes" in conn_output:
                                    device_name = "Unknown"
                                    for info_line in conn_output.split('\n'):
                                        if 'Name:' in info_line:
                                            device_name = info_line.split('Name:', 1)[1].strip()
                                            break
                                    
                                    if mac not in last_devices:
                                        self.log(f"🎉 Device connected: {device_name} ({mac})")
                                        self.log("🎵 You can now play audio!")
                
                last_devices = current_devices
                
                if not current_devices:
                    self.log("⏳ Waiting for device connection...")
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"❌ Monitor error: {e}")
                time.sleep(5)
    
    def show_status(self):
        """Display current Bluetooth status"""
        self.log("📊 Bluetooth Status:")
        self.log("=" * 50)
        
        success, output, _ = self.run_command("bluetoothctl show")
        if success:
            for line in output.split('\n'):
                if any(keyword in line for keyword in ['Powered:', 'Discoverable:', 'Pairable:', 'Alias:']):
                    status = "✅" if ("yes" in line or self.device_name in line) else "❌"
                    self.log(f"{status} {line.strip()}")
        
        self.log("=" * 50)
    
    def cleanup(self):
        """Cleanup on exit"""
        self.log("🔄 Cleaning up...")
        self.running = False
        
        # Turn off discoverable mode
        self.run_command("echo 'discoverable off' | bluetoothctl")
        self.log("✅ Cleanup complete")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Main execution"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.log("🔵 FORCE Auto-Accept Bluetooth Speaker")
        self.log("=" * 50)
        
        # Clear old pairings
        self.clear_old_pairings()
        
        # Aggressive Bluetooth setup
        if not self.setup_bluetooth_aggressive():
            self.log("❌ Failed to setup Bluetooth")
            return False
        
        time.sleep(3)
        
        # Show current status
        self.show_status()
        
        # Start aggressive pairing agent
        if not self.start_aggressive_pairing_agent():
            self.log("❌ Failed to start pairing agent")
            return False
        
        # Start D-Bus auto-accept
        self.start_dbus_auto_accept()
        
        time.sleep(2)
        
        self.log("")
        self.log("🎵 FORCE AUTO-ACCEPT BLUETOOTH SPEAKER READY!")
        self.log("=" * 50)
        self.log(f"📱 Device name: {self.device_name}")
        self.log("🔓 FORCE Auto-accept: ENABLED")
        self.log("❌ ABSOLUTELY NO PIN/CODE/CONFIRMATION required!")
        self.log("")
        self.log("📋 Instructions:")
        self.log("   1. Open Bluetooth settings on your phone")
        self.log(f"   2. Look for '{self.device_name}'")
        self.log("   3. Tap to connect - ALL prompts auto-accepted!")
        self.log("   4. Start playing audio!")
        self.log("")
        self.log("⚠️  This mode FORCES acceptance of ALL pairing requests")
        self.log("⏹️  Press Ctrl+C to stop")
        self.log("=" * 50)
        
        # Monitor connections with auto-trust
        try:
            self.monitor_and_auto_trust()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
        
        return True

if __name__ == "__main__":
    speaker = ForceAutoAcceptBluetoothSpeaker()
    try:
        speaker.run()
    except KeyboardInterrupt:
        speaker.log("Force Auto-Accept Bluetooth Speaker stopped by user")
    except Exception as e:
        speaker.log(f"Unexpected error: {e}")
    finally:
        speaker.log("Force Auto-Accept Bluetooth Speaker shutdown complete")
