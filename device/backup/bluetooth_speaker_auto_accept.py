#!/usr/bin/env python3
"""
Auto-Accept Bluetooth Speaker
Automatically accepts all pairing requests without user confirmation
"""

import subprocess
import time
import signal
import sys
import threading

class AutoAcceptBluetoothSpeaker:
    def __init__(self):
        self.device_name = "Ubuntu-Speaker"
        self.running = True
        
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
    
    def setup_bluetooth(self):
        """Configure Bluetooth with auto-accept agent"""
        self.log("🔧 Setting up Bluetooth...")
        
        # Basic Bluetooth setup commands
        commands = [
            "rfkill unblock bluetooth",  # Unblock if blocked
            "systemctl --user restart bluetooth || true",  # Restart if possible
        ]
        
        for cmd in commands:
            self.run_command(cmd)
        
        time.sleep(2)
        
        # Configure bluetoothctl
        bt_setup = """
power on
agent NoInputNoOutput
default-agent
discoverable on
pairable on
system-alias Ubuntu-Speaker
quit
"""
        
        # Execute bluetooth setup
        process = subprocess.Popen(['bluetoothctl'], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        try:
            process.communicate(input=bt_setup, timeout=15)
            self.log("✅ Bluetooth setup completed")
        except subprocess.TimeoutExpired:
            process.kill()
            self.log("⚠️  Setup timeout, but likely succeeded")
        
        return True
    
    def start_auto_accept_agent(self):
        """Start background agent that auto-accepts all pairing requests"""
        self.log("🤖 Starting auto-accept agent...")
        
        def agent_worker():
            """Background worker to handle pairing"""
            while self.running:
                try:
                    # Continuously run agent to handle pairing requests
                    agent_commands = """
agent NoInputNoOutput
default-agent
"""
                    process = subprocess.Popen(['bluetoothctl'], 
                                             stdin=subprocess.PIPE, 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE,
                                             text=True)
                    
                    process.communicate(input=agent_commands, timeout=30)
                    
                except Exception as e:
                    if self.running:  # Only log if we're still supposed to be running
                        self.log(f"Agent worker restarting: {e}")
                
                time.sleep(5)  # Wait before restarting
        
        # Start agent worker in background thread
        agent_thread = threading.Thread(target=agent_worker, daemon=True)
        agent_thread.start()
        
        return True
    
    def monitor_connections(self):
        """Monitor and report Bluetooth connections"""
        self.log("👁️  Monitoring connections...")
        
        last_connected = set()
        
        while self.running:
            try:
                # Get currently connected devices
                success, output, _ = self.run_command("bluetoothctl devices Connected")
                
                current_connected = set()
                if success and output.strip():
                    for line in output.strip().split('\n'):
                        if line.strip():
                            current_connected.add(line.strip())
                
                # Check for new connections
                new_connections = current_connected - last_connected
                for device in new_connections:
                    device_info = device.split(' ', 2)
                    if len(device_info) >= 3:
                        mac = device_info[1]
                        name = device_info[2]
                        self.log(f"🎉 Device connected: {name} ({mac})")
                        self.log("🎵 You can now play music from your phone!")
                        
                        # Auto-trust the device for future connections
                        self.run_command(f"echo 'trust {mac}' | bluetoothctl")
                        self.log(f"🔒 Device {name} is now trusted")
                
                # Check for disconnections
                disconnected = last_connected - current_connected
                for device in disconnected:
                    device_info = device.split(' ', 2)
                    if len(device_info) >= 3:
                        name = device_info[2]
                        self.log(f"📵 Device disconnected: {name}")
                
                last_connected = current_connected
                
                # Show waiting message if no connections
                if not current_connected:
                    self.log("⏳ Waiting for phone connection...")
                
                time.sleep(15)  # Check every 15 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"❌ Monitor error: {e}")
                time.sleep(10)
    
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
        
        self.log("🔵 Auto-Accept Bluetooth Speaker")
        self.log("=" * 50)
        
        # Clear old pairings
        self.clear_old_pairings()
        
        # Setup Bluetooth
        if not self.setup_bluetooth():
            self.log("❌ Failed to setup Bluetooth")
            return False
        
        time.sleep(3)
        
        # Show current status
        self.show_status()
        
        # Start auto-accept agent
        if not self.start_auto_accept_agent():
            self.log("❌ Failed to start auto-accept agent")
            return False
        
        self.log("")
        self.log("🎵 BLUETOOTH SPEAKER READY - AUTO-ACCEPT MODE!")
        self.log("=" * 50)
        self.log(f"📱 Device name: {self.device_name}")
        self.log("🔓 Auto-accept: ENABLED")
        self.log("❌ NO PIN/CODE required!")
        self.log("")
        self.log("📋 Instructions:")
        self.log("   1. Open Bluetooth settings on your phone")
        self.log(f"   2. Look for '{self.device_name}'")
        self.log("   3. Tap to connect - it pairs automatically!")
        self.log("   4. Start playing music!")
        self.log("")
        self.log("⚠️  This mode auto-accepts ALL pairing requests")
        self.log("⏹️  Press Ctrl+C to stop")
        self.log("=" * 50)
        
        # Monitor connections
        try:
            self.monitor_connections()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
        
        return True

if __name__ == "__main__":
    speaker = AutoAcceptBluetoothSpeaker()
    try:
        speaker.run()
    except KeyboardInterrupt:
        speaker.log("Bluetooth Speaker stopped by user")
    except Exception as e:
        speaker.log(f"Unexpected error: {e}")
    finally:
        speaker.log("Bluetooth Speaker shutdown complete")
