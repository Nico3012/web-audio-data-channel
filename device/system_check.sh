#!/bin/bash

# Test script to check if the system is ready for Bluetooth speaker functionality

echo "=== Bluetooth Speaker System Check ==="
echo

# Check if Bluetooth is available
echo "Checking Bluetooth availability..."
if command -v bluetoothctl &> /dev/null; then
    echo "✓ bluetoothctl is available"
    
    # Check if Bluetooth service is running
    if systemctl is-active --quiet bluetooth; then
        echo "✓ Bluetooth service is running"
    else
        echo "✗ Bluetooth service is not running"
        echo "  Try: sudo systemctl start bluetooth"
    fi
    
    # Check if Bluetooth adapter is available
    if bluetoothctl list | grep -q "Controller"; then
        echo "✓ Bluetooth adapter found"
        
        # Check if adapter is powered
        if bluetoothctl show | grep -q "Powered: yes"; then
            echo "✓ Bluetooth adapter is powered on"
        else
            echo "✗ Bluetooth adapter is powered off"
            echo "  Try: bluetoothctl power on"
        fi
    else
        echo "✗ No Bluetooth adapter found"
    fi
else
    echo "✗ bluetoothctl not found. Install with: sudo apt-get install bluez"
fi

echo

# Check PulseAudio
echo "Checking PulseAudio..."
if command -v pulseaudio &> /dev/null; then
    echo "✓ PulseAudio is available"
    
    # Check if PulseAudio is running
    if pulseaudio --check; then
        echo "✓ PulseAudio is running"
        
        # Check for Bluetooth modules
        if pactl list short modules | grep -q bluetooth; then
            echo "✓ Bluetooth modules are loaded in PulseAudio"
        else
            echo "✗ Bluetooth modules not loaded in PulseAudio"
            echo "  Try loading: pactl load-module module-bluetooth-discover"
        fi
    else
        echo "✗ PulseAudio is not running"
        echo "  Try: pulseaudio --start"
    fi
else
    echo "✗ PulseAudio not found. Install with: sudo apt-get install pulseaudio"
fi

echo

# Check required packages
echo "Checking required packages..."
packages=("bluez" "pulseaudio-module-bluetooth" "python3")

for package in "${packages[@]}"; do
    if dpkg -l | grep -q "^ii.*$package"; then
        echo "✓ $package is installed"
    else
        echo "✗ $package is not installed"
        echo "  Install with: sudo apt-get install $package"
    fi
done

echo

# Check Python dependencies
echo "Checking Python dependencies..."
if python3 -c "import pexpect" 2>/dev/null; then
    echo "✓ python3-pexpect is available"
else
    echo "✗ python3-pexpect not found"
    echo "  Install with: sudo apt-get install python3-pexpect"
fi

echo

# Check user groups
echo "Checking user permissions..."
if groups $USER | grep -q bluetooth; then
    echo "✓ User is in bluetooth group"
else
    echo "✗ User is not in bluetooth group"
    echo "  Add with: sudo usermod -a -G bluetooth $USER"
    echo "  Then log out and back in"
fi

echo

# Check audio output
echo "Checking audio output..."
if pactl list short sinks | grep -q "alsa_output"; then
    echo "✓ Audio output devices found"
    echo "Available sinks:"
    pactl list short sinks | grep alsa_output | while read line; do
        echo "  - $(echo $line | cut -d' ' -f2)"
    done
else
    echo "✗ No audio output devices found"
fi

echo
echo "=== System Check Complete ==="
echo

# Summary
errors=0

if ! command -v bluetoothctl &> /dev/null; then ((errors++)); fi
if ! systemctl is-active --quiet bluetooth; then ((errors++)); fi
if ! bluetoothctl list | grep -q "Controller"; then ((errors++)); fi
if ! command -v pulseaudio &> /dev/null; then ((errors++)); fi
if ! pulseaudio --check; then ((errors++)); fi
if ! dpkg -l | grep -q "^ii.*bluez"; then ((errors++)); fi
if ! dpkg -l | grep -q "^ii.*pulseaudio-module-bluetooth"; then ((errors++)); fi
if ! python3 -c "import pexpect" 2>/dev/null; then ((errors++)); fi

if [ $errors -eq 0 ]; then
    echo "✓ System appears ready for Bluetooth speaker functionality!"
    echo "Run './setup.sh' to complete the installation."
else
    echo "✗ Found $errors issue(s) that need to be resolved."
    echo "Please fix the issues above before proceeding."
fi
