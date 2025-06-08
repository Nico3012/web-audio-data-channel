#!/usr/bin/env python3
"""
Bluetooth Speaker with Proper Pairing Support
Handles PIN/passkey authentication correctly
"""

import subprocess
import threading
import time
import signal
import sys
import os

class BluetoothSpeakerWithPairing:
    def __init__(self):
        self.device_name = "Ubuntu-Speaker"
        self.pin_code = "0000"  # Default PIN
        self.running = True
        self.bluetoothctl_process = None
        
    def log(self, message):
        """Simple logging function"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def run_command(self, command, timeout=10):
        """Run a shell command with timeout"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def setup_bluetooth(self):
        """Configure Bluetooth for pairing"""
        self.log("🔧 Setting up Bluetooth...")
        
        commands = [
            "rfkill unblock bluetooth",  # Ensure Bluetooth is not blocked
            "systemctl --user restart bluetooth",  # Restart Bluetooth service
        ]
        
        for cmd in commands:
            success, out, err = self.run_command(cmd)
            if not success and "rfkill" not in cmd:  # rfkill might not be needed
                self.log(f"⚠️  Warning: {cmd} failed: {err}")
        
        time.sleep(2)
        
        # Configure Bluetooth with bluetoothctl
        self.log("📡 Configuring Bluetooth adapter...")
        
        bt_commands = """
power on
agent KeyboardDisplay
default-agent
discoverable on
pairable on
system-alias Ubuntu-Speaker
""".strip()
        
        # Run bluetoothctl commands
        process = subprocess.Popen(['bluetoothctl'], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        try:
            output, error = process.communicate(input=bt_commands, timeout=10)
            self.log("✅ Bluetooth configured")
        except subprocess.TimeoutExpired:
            process.kill()
            self.log("⚠️  Bluetooth configuration timed out, but may have succeeded")
        
        return True
    
    def start_pairing_agent(self):
        """Start interactive pairing agent"""
        self.log("🤖 Starting pairing agent...")
        
        def agent_thread():
            """Agent thread to handle pairing requests"""
            agent_script = f'''
import pexpect
import sys
import time

try:
    # Start bluetoothctl
    child = pexpect.spawn('bluetoothctl', timeout=300)
    child.logfile_read = sys.stdout.buffer
    
    # Set up agent
    child.sendline('agent KeyboardDisplay')
    child.expect(['Agent registered', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
    
    child.sendline('default-agent')
    child.expect(['Default agent request successful', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
    
    print("\\n🤖 Pairing agent is ready!")
    print("📱 Now try to connect from your phone...")
    
    while True:
        try:
            index = child.expect([
                'Request confirmation.*',
                'Request passkey.*', 
                'Request PIN code.*',
                'Confirm passkey.*',
                'Enter PIN code.*',
                'Authorize service.*',
                pexpect.TIMEOUT
            ], timeout=30)
            
            if index == 0:  # Request confirmation
                print("\\n✅ Confirming pairing request...")
                child.sendline('yes')
                
            elif index == 1:  # Request passkey
                print("\\n🔑 Providing passkey: {self.pin_code}")
                child.sendline('{self.pin_code}')
                
            elif index == 2:  # Request PIN code  
                print("\\n🔑 Providing PIN: {self.pin_code}")
                child.sendline('{self.pin_code}')
                
            elif index == 3:  # Confirm passkey
                print("\\n✅ Confirming passkey...")
                child.sendline('yes')
                
            elif index == 4:  # Enter PIN code
                print("\\n🔑 Entering PIN: {self.pin_code}")
                child.sendline('{self.pin_code}')
                
            elif index == 5:  # Authorize service
                print("\\n✅ Authorizing service...")
                child.sendline('yes')
                
            else:  # Timeout
                continue
                
        except pexpect.EOF:
            break
        except Exception as e:
            print(f"\\n❌ Agent error: {{e}}")
            break
            
except KeyboardInterrupt:
    print("\\n🔄 Agent stopped by user")
except Exception as e:
    print(f"\\n❌ Agent failed: {{e}}")
finally:
    try:
        child.close()
    except:
        pass
'''
            
            # Write and run the agent script
            with open('/tmp/bt_pairing_agent.py', 'w') as f:
                f.write(agent_script)
            
            try:
                subprocess.run([sys.executable, '/tmp/bt_pairing_agent.py'])
            except Exception as e:
                self.log(f"❌ Agent thread error: {e}")
        
        # Start agent in background thread
        agent_thread_obj = threading.Thread(target=agent_thread, daemon=True)
        agent_thread_obj.start()
        
        return True
    
    def monitor_connections(self):
        """Monitor Bluetooth connections"""
        self.log("👁️  Monitoring connections...")
        
        last_connected = set()
        
        while self.running:
            try:
                # Check connected devices
                success, output, _ = self.run_command("bluetoothctl devices Connected")
                
                current_connected = set()
                if success and output.strip():
                    for line in output.strip().split('\n'):
                        if line.strip():
                            current_connected.add(line.strip())
                
                # Check for new connections
                new_connections = current_connected - last_connected
                for device in new_connections:
                    device_name = device.split(' ', 2)[-1] if ' ' in device else device
                    self.log(f"🎉 Device connected: {device_name}")
                    self.log("🎵 You can now play audio from your phone!")
                
                # Check for disconnections
                disconnected = last_connected - current_connected
                for device in disconnected:
                    device_name = device.split(' ', 2)[-1] if ' ' in device else device
                    self.log(f"📵 Device disconnected: {device_name}")
                
                last_connected = current_connected
                
                # Show status every 30 seconds if no connections
                if not current_connected:
                    self.log("⏳ Waiting for phone connection...")
                
                time.sleep(30)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"❌ Monitor error: {e}")
                time.sleep(10)
    
    def show_status(self):
        """Show current Bluetooth status"""
        self.log("📊 Bluetooth Status:")
        self.log("=" * 50)
        
        success, output, _ = self.run_command("bluetoothctl show")
        if success:
            for line in output.split('\n'):
                if any(keyword in line for keyword in ['Powered:', 'Discoverable:', 'Pairable:', 'Alias:']):
                    status = "✅" if "yes" in line or "Ubuntu-Speaker" in line else "❌"
                    self.log(f"{status} {line.strip()}")
        
        self.log("=" * 50)
    
    def cleanup(self):
        """Cleanup on exit"""
        self.log("🔄 Cleaning up...")
        self.running = False
        
        # Turn off discoverable mode
        subprocess.run(['bluetoothctl'], input="discoverable off\nquit\n", 
                      text=True, capture_output=True)
        
        self.log("✅ Cleanup complete")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C"""
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Main execution"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.log("🔵 Ubuntu Bluetooth Speaker with Pairing")
        self.log("=" * 50)
        
        # Setup Bluetooth
        if not self.setup_bluetooth():
            self.log("❌ Failed to setup Bluetooth")
            return False
        
        time.sleep(3)
        
        # Show status
        self.show_status()
        
        # Start pairing agent
        if not self.start_pairing_agent():
            self.log("❌ Failed to start pairing agent")
            return False
        
        time.sleep(2)
        
        self.log("")
        self.log("🎵 BLUETOOTH SPEAKER READY!")
        self.log("=" * 50)
        self.log("📱 Device name: Ubuntu-Speaker")
        self.log(f"🔑 PIN code: {self.pin_code}")
        self.log("")
        self.log("📋 Instructions:")
        self.log("   1. Open Bluetooth settings on your phone")
        self.log("   2. Look for 'Ubuntu-Speaker'")
        self.log("   3. When prompted, enter PIN: " + self.pin_code)
        self.log("   4. Start playing music!")
        self.log("")
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
    speaker = BluetoothSpeakerWithPairing()
    speaker.run()
