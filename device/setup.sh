#!/bin/bash

# Bluetooth Speaker Setup Script
# This script installs and configures required packages for manual Bluetooth speaker operation

set -e

echo "=== Ubuntu Bluetooth Speaker Setup ==="
echo "This script will set up your laptop for manual Bluetooth speaker operation"
echo "No background services will be created - programs run only when you start them"
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

# Enable and start Bluetooth service (system service, not our application)
echo "Enabling Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Make our programs executable
echo "Making Bluetooth speaker programs executable..."
chmod +x bluetooth_pairing.py bluetooth_player.py

echo
echo "=== Setup Complete! ==="
echo
echo "Your laptop is now configured for manual Bluetooth speaker operation."
echo
echo "To use:"
echo "1. First time: Run ./bluetooth_pairing.py to pair your phone"
echo "2. Daily use: Run ./bluetooth_player.py to receive audio"
echo "3. Audio will play through your laptop speakers"
echo
echo "Programs only run when you manually start them - no background services."
echo
echo "Note: You may need to log out and back in for group membership to take effect."
echo "Or run: newgrp bluetooth"
