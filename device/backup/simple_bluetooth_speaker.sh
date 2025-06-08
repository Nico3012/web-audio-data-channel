#!/bin/bash

# Simple Bluetooth Speaker Script
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
    bluetoothctl discoverable off 2>/dev/null
    echo "✅ Bluetooth Speaker stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Configure Bluetooth
echo "🔧 Configuring Bluetooth..."

# Power on, make discoverable and pairable
bluetoothctl power on
bluetoothctl agent NoInputNoOutput
bluetoothctl default-agent
bluetoothctl discoverable on
bluetoothctl pairable on
bluetoothctl system-alias "Ubuntu-Speaker"

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

while true; do
    # Check for connected devices
    connected=$(bluetoothctl devices Connected 2>/dev/null)
    
    if [ ! -z "$connected" ]; then
        echo "📱 Connected devices:"
        echo "$connected" | while read line; do
            if [ ! -z "$line" ]; then
                echo "   ✅ $line"
            fi
        done
        echo
    fi
    
    sleep 10
done
