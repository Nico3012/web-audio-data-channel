#!/bin/bash

# Working Bluetooth Speaker Script
# Makes Ubuntu laptop discoverable as Bluetooth speaker

echo "🔵 Ubuntu Bluetooth Speaker Starting..."
echo "======================================"

# Check if Bluetooth is available
if ! command -v bluetoothctl &> /dev/null; then
    echo "❌ bluetoothctl not found. Please install: sudo apt install bluez"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo
    echo "🔄 Cleaning up..."
    echo "discoverable off" | bluetoothctl
    echo "✅ Bluetooth Speaker stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Configure Bluetooth using echo pipes to avoid hanging
echo "🔧 Configuring Bluetooth..."

# Power on
echo "power on" | bluetoothctl
sleep 1

# Make discoverable and pairable
echo "discoverable on" | bluetoothctl
sleep 1
echo "pairable on" | bluetoothctl
sleep 1

# Set device name
echo "system-alias Ubuntu-Speaker" | bluetoothctl
sleep 1

# Check status
echo
echo "📊 Bluetooth Status:"
echo "==================="
bluetoothctl show | grep -E "(Name|Alias|Powered|Discoverable|Pairable)"

echo
echo "🎵 BLUETOOTH SPEAKER READY!"
echo "=========================="
echo "📱 Device name: Ubuntu-Speaker"
echo "🔍 Your laptop is now discoverable"
echo ""
echo "📋 To connect from your phone:"
echo "   1. Open Bluetooth settings"
echo "   2. Look for 'Ubuntu-Speaker'"
echo "   3. Connect to it"
echo "   4. Start playing music!"
echo ""
echo "🎧 Audio will automatically play through your laptop speakers"
echo "⏹️  Press Ctrl+C to stop"
echo

# Monitor for connections
echo "👁️  Monitoring connections..."
echo "=============================="

# Simple loop to keep the script running and show status
while true; do
    # Check for connected devices every 15 seconds
    sleep 15
    
    connected=$(bluetoothctl devices Connected 2>/dev/null | head -5)
    
    if [ ! -z "$connected" ]; then
        echo "📱 $(date '+%H:%M:%S') - Connected devices:"
        echo "$connected" | while read line; do
            if [ ! -z "$line" ]; then
                device_name=$(echo "$line" | cut -d' ' -f3-)
                echo "   ✅ $device_name"
            fi
        done
        echo
    else
        echo "⏳ $(date '+%H:%M:%S') - Waiting for connections..."
    fi
done
