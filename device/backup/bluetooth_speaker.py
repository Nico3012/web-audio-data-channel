#!/usr/bin/env python3
"""
Bluetooth Speaker Controller
Turns Ubuntu laptop into a Bluetooth A2DP sink (speaker)
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
        
    def run_command(self, command, shell=True):
        """Execute shell command and return result"""
        try:
            result = subprocess.run(command, shell=shell, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Command failed: {command}")
                logging.error(f"Error: {result.stderr}")
                return False, result.stderr
            return True, result.stdout
        except Exception as e:
            logging.error(f"Exception running command {command}: {e}")
            return False, str(e)
    
    def check_dependencies(self):
        """Check if required packages are installed"""
        required_packages = ['bluez', 'pulseaudio-module-bluetooth']
        missing_packages = []
        
        for package in required_packages:
            success, _ = self.run_command(f"dpkg -l | grep {package}")
            if not success:
                missing_packages.append(package)
        
        if missing_packages:
            logging.error(f"Missing packages: {missing_packages}")
            logging.info("Please install missing packages with:")
            logging.info(f"sudo apt-get install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def setup_bluetooth_config(self):
        """Configure Bluetooth for A2DP sink"""
        logging.info("Setting up Bluetooth configuration...")
        
        # Enable Bluetooth
        success, _ = self.run_command("sudo systemctl enable bluetooth")
        if not success:
            return False
            
        success, _ = self.run_command("sudo systemctl start bluetooth")
        if not success:
            return False
        
        # Power on Bluetooth adapter
        success, _ = self.run_command("sudo bluetoothctl power on")
        if not success:
            return False
        
        # Make discoverable
        success, _ = self.run_command("sudo bluetoothctl discoverable on")
        if not success:
            return False
        
        # Make pairable
        success, _ = self.run_command("sudo bluetoothctl pairable on")
        if not success:
            return False
        
        # Set device name
        success, _ = self.run_command(f"sudo bluetoothctl system-alias '{self.bt_device_name}'")
        if not success:
            logging.warning("Could not set device name")
        
        logging.info("Bluetooth configuration completed")
        return True
    
    def setup_pulseaudio(self):
        """Configure PulseAudio for Bluetooth A2DP"""
        logging.info("Setting up PulseAudio...")
        
        # Load Bluetooth modules
        modules = [
            "module-bluetooth-policy",
            "module-bluetooth-discover"
        ]
        
        for module in modules:
            success, _ = self.run_command(f"pactl load-module {module}")
            if success:
                logging.info(f"Loaded module: {module}")
            else:
                logging.warning(f"Could not load module: {module} (might already be loaded)")
        
        # Restart PulseAudio to ensure all modules are loaded
        success, _ = self.run_command("pulseaudio -k")
        time.sleep(2)
        success, _ = self.run_command("pulseaudio --start")
        
        logging.info("PulseAudio setup completed")
        return True
    
    def start_agent(self):
        """Start Bluetooth agent for auto-pairing"""
        logging.info("Starting Bluetooth agent...")
        
        # Start agent that accepts all pairing requests
        agent_script = f"""
import pexpect
import sys

try:
    child = pexpect.spawn('bluetoothctl')
    child.expect('#')
    child.sendline('agent NoInputNoOutput')
    child.expect('#')
    child.sendline('default-agent')
    child.expect('#')
    
    while True:
        index = child.expect(['Request confirmation', 'Request passkey', 'Request PIN', pexpect.TIMEOUT], timeout=30)
        if index == 0:  # Request confirmation
            child.sendline('yes')
        elif index == 1:  # Request passkey
            child.sendline('0000')
        elif index == 2:  # Request PIN
            child.sendline('0000')
        else:  # Timeout
            continue
            
except KeyboardInterrupt:
    child.close()
    sys.exit(0)
except Exception as e:
    print(f"Agent error: {{e}}")
    sys.exit(1)
"""
        
        with open('/tmp/bt_agent.py', 'w') as f:
            f.write(agent_script)
        
        # Start the agent in background
        subprocess.Popen([sys.executable, '/tmp/bt_agent.py'])
        
        return True
    
    def monitor_connections(self):
        """Monitor for new Bluetooth connections and set up audio routing"""
        logging.info("Monitoring for Bluetooth connections...")
        
        while self.running:
            try:
                # Check for connected devices
                success, output = self.run_command("bluetoothctl info")
                
                if success and "Connected: yes" in output:
                    # Get connected device info
                    success, devices = self.run_command("bluetoothctl devices Connected")
                    if success and devices.strip():
                        logging.info("Device connected, setting up audio routing...")
                        self.setup_audio_routing()
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Error in monitoring: {e}")
                time.sleep(5)
    
    def setup_audio_routing(self):
        """Set up audio routing for connected Bluetooth device"""
        # Set default sink to speakers
        success, sinks = self.run_command("pactl list short sinks")
        if success:
            for line in sinks.split('\n'):
                if 'alsa_output' in line and 'analog-stereo' in line:
                    sink_name = line.split()[1]
                    self.run_command(f"pactl set-default-sink {sink_name}")
                    logging.info(f"Set default sink to: {sink_name}")
                    break
        
        # Ensure Bluetooth source is connected to speakers
        success, sources = self.run_command("pactl list short sources")
        if success:
            for line in sources.split('\n'):
                if 'bluez' in line:
                    source_name = line.split()[1]
                    # Create loopback from Bluetooth source to speakers
                    self.run_command(f"pactl load-module module-loopback source={source_name}")
                    logging.info(f"Created loopback for Bluetooth source: {source_name}")
                    break
    
    def enter_pairing_mode(self):
        """Enter pairing mode"""
        logging.info("Entering pairing mode...")
        
        # Make discoverable and pairable
        self.run_command("bluetoothctl discoverable on")
        self.run_command("bluetoothctl pairable on")
        
        logging.info("Device is now discoverable and pairable")
        logging.info(f"Look for '{self.bt_device_name}' on your phone's Bluetooth settings")
        
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
        
        # Check dependencies
        if not self.check_dependencies():
            logging.error("Missing dependencies. Please install required packages.")
            return False
        
        # Setup Bluetooth
        if not self.setup_bluetooth_config():
            logging.error("Failed to setup Bluetooth")
            return False
        
        # Setup PulseAudio
        if not self.setup_pulseaudio():
            logging.error("Failed to setup PulseAudio")
            return False
        
        # Start agent
        if not self.start_agent():
            logging.error("Failed to start Bluetooth agent")
            return False
        
        # Enter pairing mode
        if not self.enter_pairing_mode():
            logging.error("Failed to enter pairing mode")
            return False
        
        logging.info("Bluetooth Speaker is ready!")
        logging.info("Connect from your phone to start playing audio")
        
        # Monitor connections
        self.monitor_connections()
        
        return True

if __name__ == "__main__":
    speaker = BluetoothSpeaker()
    speaker.run()
