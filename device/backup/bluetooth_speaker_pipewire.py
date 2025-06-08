#!/usr/bin/env python3
"""
Bluetooth Speaker Controller - PipeWire Compatible Version
Turns Ubuntu laptop into a Bluetooth A2DP sink (speaker)
Works with both PulseAudio and PipeWire
"""

import subprocess
import time
import logging
import signal
import sys
import os
import configparser
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/bluetooth_speaker.log'),
        logging.StreamHandler()
    ]
)

class BluetoothSpeaker:
    def __init__(self, config_file="config.ini"):
        # Load configuration
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load_config()
        
        self.bt_device_name = self.config.get('bluetooth', 'device_name', fallback="Ubuntu-Speaker")
        self.bt_class = self.config.get('bluetooth', 'device_class', fallback="0x200414")
        self.auto_accept_pairing = self.config.getboolean('bluetooth', 'auto_accept_pairing', fallback=True)
        self.pairing_pin = self.config.get('bluetooth', 'pairing_pin', fallback="0000")
        self.running = True
        self.is_pipewire = self.detect_pipewire()
        
    def detect_pipewire(self):
        """Detect if we're running PipeWire or PulseAudio"""
        try:
            result = subprocess.run(['pactl', 'info'], capture_output=True, text=True)
            if 'PipeWire' in result.stdout:
                logging.info("Detected PipeWire audio system")
                return True
            else:
                logging.info("Detected PulseAudio audio system")
                return False
        except:
            return False
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            # Create default config if it doesn't exist
            self.create_default_config()

    def create_default_config(self):
        """Create default configuration file"""
        self.config['bluetooth'] = {
            'device_name': 'Ubuntu-Speaker',
            'device_class': '0x200414',
            'auto_accept_pairing': 'true',
            'pairing_pin': '0000',
            'max_connections': '1'
        }
        self.config['audio'] = {
            'sample_rate': '44100',
            'buffer_size': '1024',
            'audio_format': '16bit',
            'adaptive_bitrate': 'true'
        }
        self.config['pulseaudio'] = {
            'auto_route_to_speakers': 'true',
            'enable_loopback': 'true',
            'default_sink': 'auto'
        }
        self.config['logging'] = {
            'log_level': 'INFO',
            'log_file': '/tmp/bluetooth_speaker.log',
            'console_output': 'true'
        }
        
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        
    def run_command(self, command, shell=True, check_sudo=False):
        """Execute shell command and return result"""
        try:
            if check_sudo and 'sudo' in command:
                logging.warning(f"Skipping sudo command in user mode: {command}")
                return True, ""
            
            result = subprocess.run(command, shell=shell, capture_output=True, text=True)
            if result.returncode != 0:
                logging.warning(f"Command failed: {command}")
                logging.warning(f"Error: {result.stderr}")
                return False, result.stderr
            return True, result.stdout
        except Exception as e:
            logging.error(f"Exception running command {command}: {e}")
            return False, str(e)
    
    def check_dependencies(self):
        """Check if required packages are installed"""
        # Check if Bluetooth is available
        success, _ = self.run_command("which bluetoothctl")
        if not success:
            logging.error("bluetoothctl not found. Please install bluez package.")
            return False
        
        # Check if audio system is running
        success, _ = self.run_command("pactl info")
        if not success:
            logging.error("PulseAudio/PipeWire not running.")
            return False
            
        return True
    
    def setup_bluetooth_basic(self):
        """Configure Bluetooth without sudo (user-level commands only)"""
        logging.info("Setting up Bluetooth configuration...")
        
        # Check if Bluetooth is powered on
        success, output = self.run_command("bluetoothctl show")
        if success and "Powered: no" in output:
            logging.warning("Bluetooth adapter is powered off. You may need to run: bluetoothctl power on")
        
        # Basic bluetoothctl commands that don't require sudo
        commands = [
            "bluetoothctl power on",
            "bluetoothctl discoverable on", 
            "bluetoothctl pairable on",
            f"bluetoothctl system-alias '{self.bt_device_name}'"
        ]
        
        for cmd in commands:
            success, output = self.run_command(cmd)
            if success:
                logging.info(f"✓ {cmd}")
            else:
                logging.warning(f"✗ {cmd} - {output}")
        
        return True
    
    def start_bluetooth_agent(self):
        """Start a simple Bluetooth agent using bluetoothctl"""
        logging.info("Starting Bluetooth agent...")
        
        # Create a simple agent script
        agent_commands = f"""
import subprocess
import time
import sys

try:
    # Start bluetoothctl in interactive mode
    proc = subprocess.Popen(['bluetoothctl'], 
                           stdin=subprocess.PIPE, 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           text=True)
    
    # Send agent commands
    proc.stdin.write('agent NoInputNoOutput\\n')
    proc.stdin.flush()
    time.sleep(1)
    
    proc.stdin.write('default-agent\\n')
    proc.stdin.flush()
    time.sleep(1)
    
    # Keep it running
    while True:
        time.sleep(10)
        
except KeyboardInterrupt:
    if proc:
        proc.terminate()
    sys.exit(0)
except Exception as e:
    print(f"Agent error: {{e}}")
    sys.exit(1)
"""
        
        # Write and start the agent
        with open('/tmp/bt_simple_agent.py', 'w') as f:
            f.write(agent_commands)
        
        # Start the agent in background
        try:
            subprocess.Popen([sys.executable, '/tmp/bt_simple_agent.py'])
            logging.info("Bluetooth agent started")
            return True
        except Exception as e:
            logging.error(f"Failed to start agent: {e}")
            return False
    
    def monitor_bluetooth_connections(self):
        """Monitor for Bluetooth audio connections"""
        logging.info("Monitoring for Bluetooth connections...")
        logging.info(f"Your device '{self.bt_device_name}' is now discoverable!")
        logging.info("Connect from your phone and start playing audio.")
        
        last_devices = set()
        
        while self.running:
            try:
                # Get connected devices
                success, output = self.run_command("bluetoothctl devices Connected")
                current_devices = set()
                
                if success and output.strip():
                    for line in output.strip().split('\\n'):
                        if line.strip():
                            current_devices.add(line.strip())
                
                # Check for new connections
                new_devices = current_devices - last_devices
                if new_devices:
                    for device in new_devices:
                        logging.info(f"New device connected: {device}")
                        self.handle_new_connection(device)
                
                # Check for disconnections
                disconnected = last_devices - current_devices
                if disconnected:
                    for device in disconnected:
                        logging.info(f"Device disconnected: {device}")
                
                last_devices = current_devices
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Error in monitoring: {e}")
                time.sleep(5)
    
    def handle_new_connection(self, device_info):
        """Handle new Bluetooth connection"""
        logging.info("Setting up audio routing for new connection...")
        
        # For PipeWire/PulseAudio, the audio routing should happen automatically
        # But we can try to ensure the default sink is set correctly
        
        success, sinks = self.run_command("pactl list short sinks")
        if success:
            # Find the best audio output (usually analog-stereo)
            for line in sinks.split('\\n'):
                if 'analog-stereo' in line and 'alsa_output' in line:
                    sink_name = line.split()[1]
                    self.run_command(f"pactl set-default-sink {sink_name}")
                    logging.info(f"Set default audio sink to: {sink_name}")
                    break
    
    def enter_pairing_mode(self):
        """Enter pairing mode"""
        logging.info("Entering pairing mode...")
        
        # Make discoverable and pairable
        self.run_command("bluetoothctl discoverable on")
        self.run_command("bluetoothctl pairable on")
        
        logging.info("=" * 50)
        logging.info(f"🔵 BLUETOOTH SPEAKER READY!")
        logging.info(f"📱 Device name: '{self.bt_device_name}'")
        logging.info("🔍 Your laptop is now discoverable")
        logging.info("📋 To connect:")
        logging.info("   1. Open Bluetooth settings on your phone")
        logging.info(f"   2. Look for '{self.bt_device_name}'")
        logging.info("   3. Connect to it")
        logging.info("   4. Start playing music!")
        logging.info("=" * 50)
        
        return True
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info("Shutting down Bluetooth speaker...")
        self.running = False
    
    def run(self):
        """Main run loop"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logging.info("Starting Bluetooth Speaker setup...")
        logging.info(f"Audio system: {'PipeWire' if self.is_pipewire else 'PulseAudio'}")
        
        # Check dependencies
        if not self.check_dependencies():
            logging.error("Missing dependencies or services not running.")
            return False
        
        # Setup Bluetooth (basic user-level setup)
        if not self.setup_bluetooth_basic():
            logging.error("Failed to setup Bluetooth")
            return False
        
        # Start agent
        if not self.start_bluetooth_agent():
            logging.warning("Could not start automatic pairing agent")
        
        # Enter pairing mode
        if not self.enter_pairing_mode():
            logging.error("Failed to enter pairing mode")
            return False
        
        # Monitor connections
        self.monitor_bluetooth_connections()
        
        return True

if __name__ == "__main__":
    speaker = BluetoothSpeaker()
    try:
        speaker.run()
    except KeyboardInterrupt:
        logging.info("Bluetooth Speaker stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        logging.info("Bluetooth Speaker shutdown complete")
