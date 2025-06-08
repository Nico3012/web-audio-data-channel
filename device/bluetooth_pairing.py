#!/usr/bin/env python3
"""
Bluetooth Speaker - Pairing Mode
Enables pairing mode so new devices can connect to your laptop as a Bluetooth speaker
"""

import subprocess
import time
import signal
import sys

class BluetoothPairing:
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
    
    def setup_pairing_mode(self):
        """Enable pairing mode for new device connections"""
        self.log("🔧 Setting up pairing mode...")
        
        # Basic Bluetooth setup
        commands = [
            "rfkill unblock bluetooth",
            "systemctl --user restart bluetooth || true",
        ]
        
        for cmd in commands:
            self.run_command(cmd)
        
        time.sleep(2)
        
        # Configure bluetoothctl for pairing
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
            self.log("✅ Pairing mode enabled")
        except subprocess.TimeoutExpired:
            process.kill()
            self.log("⚠️  Setup timeout, but likely succeeded")
        
        return True
    
    def show_status(self):
        """Show current Bluetooth status"""
        self.log("📊 Bluetooth Status:")
        print("=" * 50)
        
        # Get bluetooth status
        success, output, _ = self.run_command("bluetoothctl show")
        if success:
            for line in output.split('\n'):
                if 'Alias:' in line:
                    print(f"✅ {line.strip()}")
                elif 'Powered:' in line:
                    print(f"✅ {line.strip()}")
                elif 'Discoverable:' in line:
                    print(f"✅ {line.strip()}")
                elif 'Pairable:' in line:
                    print(f"✅ {line.strip()}")
        
        print("=" * 50)
    
    def monitor_pairing(self):
        """Monitor for new pairing attempts"""
        self.log("👁️  Monitoring for pairing requests...")
        self.log("⏳ Waiting for devices to connect...")
        
        while self.running:
            try:
                # Check for new devices
                success, output, _ = self.run_command("bluetoothctl devices")
                
                if success and output.strip():
                    for line in output.strip().split('\n'):
                        if line.strip() and 'Device' in line:
                            parts = line.split(' ', 2)
                            if len(parts) >= 3:
                                mac = parts[1]
                                name = parts[2]
                                
                                # Check if device is connected
                                conn_success, conn_output, _ = self.run_command(f"bluetoothctl info {mac}")
                                if conn_success and "Connected: yes" in conn_output:
                                    self.log(f"🎉 Device paired and connected: {name} ({mac})")
                                    # Auto-trust for future connections
                                    self.run_command(f"echo 'trust {mac}' | bluetoothctl")
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Monitoring error: {e}")
                time.sleep(5)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.log("🛑 Stopping pairing mode...")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Main function to run pairing mode"""
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print()
        self.log("🔵 Bluetooth Speaker - Pairing Mode")
        print("=" * 50)
        
        # Clear old pairings
        self.clear_old_pairings()
        
        # Setup pairing mode
        if not self.setup_pairing_mode():
            self.log("❌ Failed to setup pairing mode")
            return False
        
        time.sleep(3)
        
        # Show status
        self.show_status()
        
        print()
        self.log("🎵 PAIRING MODE ACTIVE!")
        print("=" * 50)
        print(f"📱 Device name: {self.device_name}")
        print("🔓 Auto-accept: ENABLED")
        print("❌ NO PIN/CODE required!")
        print()
        print("📋 Instructions:")
        print("   1. Open Bluetooth settings on your phone")
        print("   2. Look for 'Ubuntu-Speaker'")
        print("   3. Tap to connect - it pairs automatically!")
        print("   4. Use bluetooth_player.py to play audio")
        print()
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        # Monitor for pairing
        self.monitor_pairing()
        
        return True

if __name__ == "__main__":
    pairing = BluetoothPairing()
    pairing.run()
