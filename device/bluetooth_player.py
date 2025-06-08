#!/usr/bin/env python3
"""
Bluetooth Speaker - Audio Player
Connects to already paired devices and routes audio to laptop speakers
"""

import subprocess
import time
import signal
import sys

class BluetoothPlayer:
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
    
    def setup_bluetooth(self):
        """Basic Bluetooth setup for audio playback"""
        self.log("🔧 Setting up Bluetooth for audio...")
        
        # Basic Bluetooth setup
        commands = [
            "rfkill unblock bluetooth",
            "systemctl --user restart bluetooth || true",
        ]
        
        for cmd in commands:
            self.run_command(cmd)
        
        time.sleep(2)
        
        # Configure bluetoothctl for audio
        bt_setup = """
power on
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
            process.communicate(input=bt_setup, timeout=10)
            self.log("✅ Bluetooth audio setup completed")
        except subprocess.TimeoutExpired:
            process.kill()
            self.log("⚠️  Setup timeout, but likely succeeded")
        
        return True
    
    def list_paired_devices(self):
        """List all paired devices"""
        self.log("📱 Checking paired devices...")
        
        success, output, _ = self.run_command("bluetoothctl paired-devices")
        devices = []
        
        if success and output.strip():
            print("📋 Paired devices:")
            for line in output.strip().split('\n'):
                if line.strip() and 'Device' in line:
                    parts = line.split(' ', 2)
                    if len(parts) >= 3:
                        mac = parts[1]
                        name = parts[2]
                        devices.append((mac, name))
                        print(f"   • {name} ({mac})")
        else:
            print("   No paired devices found")
            
        return devices
    
    def connect_to_devices(self, devices):
        """Connect to paired devices"""
        if not devices:
            self.log("❌ No paired devices to connect to")
            return False
        
        self.log("🔗 Connecting to paired devices...")
        
        for mac, name in devices:
            self.log(f"Connecting to {name}...")
            success, _, _ = self.run_command(f"echo 'connect {mac}' | bluetoothctl")
            if success:
                self.log(f"✅ Connected to {name}")
            else:
                self.log(f"⚠️  Could not connect to {name}")
                
        return True
    
    def show_audio_status(self):
        """Show current audio setup"""
        self.log("🎵 Audio Status:")
        print("=" * 50)
        
        # Show available audio sinks
        success, output, _ = self.run_command("pactl list short sinks")
        if success and output.strip():
            print("🔊 Available audio outputs:")
            for line in output.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        print(f"   • {parts[1]}")
        
        print("=" * 50)
    
    def monitor_connections(self):
        """Monitor connected devices and audio"""
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
                        name = device_info[2]
                        self.log(f"🎉 Device connected: {name}")
                        self.log("🎵 Ready to receive audio!")
                
                # Check for disconnections
                lost_connections = last_connected - current_connected
                for device in lost_connections:
                    device_info = device.split(' ', 2)
                    if len(device_info) >= 3:
                        name = device_info[2]
                        self.log(f"📱 Device disconnected: {name}")
                
                last_connected = current_connected
                
                # Show connection status
                if current_connected:
                    if len(current_connected) != len(last_connected):  # Status changed
                        print("\n" + "=" * 50)
                        print("📱 Currently connected devices:")
                        for device in current_connected:
                            device_info = device.split(' ', 2)
                            if len(device_info) >= 3:
                                name = device_info[2]
                                print(f"   • {name}")
                        print("🎵 Play music from your phone - audio will play through laptop speakers!")
                        print("=" * 50)
                else:
                    if last_connected:  # Just lost all connections
                        print("\n📱 No devices currently connected")
                        print("💡 Run bluetooth_pairing.py to pair new devices")
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Monitoring error: {e}")
                time.sleep(5)
    
    def cleanup_bluetooth(self):
        """Clean up Bluetooth connections, audio routes, and disable discoverable mode"""
        self.log("🧹 Cleaning up Bluetooth connections and audio routes...")
        
        try:
            # Stop all audio applications first
            self.log("🎵 Stopping audio applications...")
            self.run_command("pkill -f pulseaudio", timeout=5)
            self.run_command("pkill -f pipewire", timeout=5)
            time.sleep(1)
            
            # Get currently connected devices and disconnect them
            success, output, _ = self.run_command("bluetoothctl devices Connected")
            if success and output.strip():
                for line in output.strip().split('\n'):
                    if line.strip() and 'Device' in line:
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            mac = parts[1]
                            name = parts[2]
                            self.log(f"Disconnecting {name}...")
                            self.run_command(f"echo 'disconnect {mac}' | bluetoothctl")
            
            # Clean up audio system
            self.log("🔊 Cleaning up audio system...")
            
            # Remove Bluetooth audio modules from PulseAudio
            audio_cleanup_commands = [
                "pactl unload-module module-bluetooth-discover",
                "pactl unload-module module-bluetooth-policy", 
                "pactl unload-module module-bluez5-discover",
                "pactl unload-module module-bluez5-device",
            ]
            
            for cmd in audio_cleanup_commands:
                self.run_command(cmd, timeout=5)
            
            # Reset audio to default state
            self.run_command("pactl set-default-sink @DEFAULT_SINK@", timeout=5)
            
            # Restart audio system to clean state
            self.log("🔄 Restarting audio system...")
            self.run_command("systemctl --user restart pulseaudio", timeout=10)
            time.sleep(2)
            
            # Reset Bluetooth to non-discoverable state
            bt_cleanup = """
discoverable off
pairable off
quit
"""
            
            process = subprocess.Popen(['bluetoothctl'], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            try:
                process.communicate(input=bt_cleanup, timeout=10)
                self.log("✅ Bluetooth cleaned up")
            except subprocess.TimeoutExpired:
                process.kill()
                self.log("⚠️  Cleanup timeout, but likely succeeded")
                
            # Power cycle Bluetooth to ensure clean state
            self.log("🔄 Power cycling Bluetooth...")
            bt_power_cycle = """
power off
power on
quit
"""
            
            process = subprocess.Popen(['bluetoothctl'], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            try:
                process.communicate(input=bt_power_cycle, timeout=10)
                self.log("✅ Bluetooth power cycled")
            except subprocess.TimeoutExpired:
                process.kill()
                self.log("⚠️  Power cycle timeout")
            
            self.log("✅ Complete cleanup finished - Bluetooth speaker mode disabled")
                
        except Exception as e:
            self.log(f"Cleanup error: {e}")

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.log("🛑 Stopping audio player...")
        self.running = False
        self.cleanup_bluetooth()
        sys.exit(0)
    
    def run(self):
        """Main function to run audio player"""
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print()
        self.log("🎵 Bluetooth Speaker - Audio Player")
        print("=" * 50)
        
        # Setup bluetooth
        if not self.setup_bluetooth():
            self.log("❌ Failed to setup Bluetooth")
            return False
        
        time.sleep(2)
        
        # List paired devices
        devices = self.list_paired_devices()
        
        # Connect to devices
        if devices:
            self.connect_to_devices(devices)
            time.sleep(3)
        
        # Show audio status
        self.show_audio_status()
        
        print()
        self.log("🎵 AUDIO PLAYER ACTIVE!")
        print("=" * 50)
        print(f"📱 Device name: {self.device_name}")
        print("🔊 Audio output: Laptop speakers")
        print()
        if devices:
            print("📋 Ready to receive audio from paired devices:")
            for mac, name in devices:
                print(f"   • {name}")
        else:
            print("📋 No paired devices found")
            print("💡 Run bluetooth_pairing.py first to pair devices")
        print()
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        # Monitor connections
        self.monitor_connections()
        
        return True

if __name__ == "__main__":
    player = BluetoothPlayer()
    try:
        player.run()
    except Exception as e:
        player.log(f"Error: {e}")
    finally:
        # Ensure cleanup always happens
        player.cleanup_bluetooth()
