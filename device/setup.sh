#!/bin/bash

# Bluetooth Speaker Setup Script
# This script installs and configures required packages for Bluetooth A2DP sink

set -e

echo "=== Ubuntu Bluetooth Speaker Setup ==="
echo "This script will set up your laptop as a Bluetooth speaker"
echo

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "Please don't run this script as root. Use your regular user account."
   exit 1
fi

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install required packages
echo "Installing required packages..."
sudo apt-get install -y \
    bluez \
    pulseaudio \
    pulseaudio-module-bluetooth \
    bluetooth \
    python3 \
    python3-pexpect \
    pavucontrol

# Add user to bluetooth group
echo "Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

# Enable and start Bluetooth service
echo "Enabling Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Configure PulseAudio for Bluetooth
echo "Configuring PulseAudio..."

# Create PulseAudio config directory if it doesn't exist
mkdir -p ~/.config/pulse

# Add Bluetooth modules to PulseAudio config
cat > ~/.config/pulse/default.pa << 'EOF'
#!/usr/bin/pulseaudio -nF

# Load default configuration
.include /etc/pulse/default.pa

# Load Bluetooth modules
load-module module-bluetooth-policy
load-module module-bluetooth-discover
EOF

# Create systemd service for Bluetooth speaker
echo "Creating systemd service..."
sudo tee /etc/systemd/system/bluetooth-speaker.service > /dev/null << EOF
[Unit]
Description=Bluetooth A2DP Speaker Service
After=bluetooth.service pulseaudio.service
Requires=bluetooth.service

[Service]
Type=simple
User=$USER
Group=bluetooth
WorkingDirectory=/home/$USER/Schreibtisch/web-audio-data-channel/device
ExecStart=/usr/bin/python3 /home/$USER/Schreibtisch/web-audio-data-channel/device/bluetooth_speaker.py
Restart=always
RestartSec=5
Environment=PULSE_RUNTIME_PATH=/run/user/$(id -u)/pulse

[Install]
WantedBy=multi-user.target
EOF

# Make the Python script executable
chmod +x bluetooth_speaker.py

# Create a simple control script
cat > bluetooth_speaker_control.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        echo "Starting Bluetooth Speaker service..."
        sudo systemctl start bluetooth-speaker
        sudo systemctl status bluetooth-speaker
        ;;
    stop)
        echo "Stopping Bluetooth Speaker service..."
        sudo systemctl stop bluetooth-speaker
        ;;
    restart)
        echo "Restarting Bluetooth Speaker service..."
        sudo systemctl restart bluetooth-speaker
        sudo systemctl status bluetooth-speaker
        ;;
    status)
        sudo systemctl status bluetooth-speaker
        ;;
    enable)
        echo "Enabling Bluetooth Speaker service to start on boot..."
        sudo systemctl enable bluetooth-speaker
        ;;
    disable)
        echo "Disabling Bluetooth Speaker service from starting on boot..."
        sudo systemctl disable bluetooth-speaker
        ;;
    logs)
        sudo journalctl -u bluetooth-speaker -f
        ;;
    manual)
        echo "Running Bluetooth Speaker manually..."
        python3 bluetooth_speaker.py
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|logs|manual}"
        echo
        echo "Commands:"
        echo "  start   - Start the Bluetooth speaker service"
        echo "  stop    - Stop the Bluetooth speaker service"
        echo "  restart - Restart the Bluetooth speaker service"
        echo "  status  - Show service status"
        echo "  enable  - Enable service to start on boot"
        echo "  disable - Disable service from starting on boot"
        echo "  logs    - Show service logs (live)"
        echo "  manual  - Run manually in terminal"
        exit 1
        ;;
esac
EOF

chmod +x bluetooth_speaker_control.sh

# Restart PulseAudio to load new configuration
echo "Restarting PulseAudio..."
# Kill PulseAudio if it's running (ignore errors if not running)
pulseaudio -k 2>/dev/null || true
sleep 2
# Start PulseAudio
if ! pulseaudio --check; then
    pulseaudio --start
    echo "PulseAudio started successfully"
else
    echo "PulseAudio is already running"
fi

echo
echo "=== Setup Complete! ==="
echo
echo "Your laptop is now configured as a Bluetooth speaker."
echo
echo "To use:"
echo "1. Run: ./bluetooth_speaker_control.sh start"
echo "2. On your phone, look for 'Ubuntu-Speaker' in Bluetooth settings"
echo "3. Connect and start playing audio!"
echo
echo "Useful commands:"
echo "  ./bluetooth_speaker_control.sh manual  - Run interactively"
echo "  ./bluetooth_speaker_control.sh logs    - View logs"
echo "  ./bluetooth_speaker_control.sh status  - Check status"
echo
echo "Note: You may need to log out and back in for group membership to take effect."
echo "Or run: newgrp bluetooth"
