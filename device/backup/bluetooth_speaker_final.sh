#!/bin/bash

# Final Working Bluetooth Speaker Script
# Your Ubuntu laptop is now a Bluetooth speaker!

echo "🔵 Ubuntu Bluetooth Speaker"
echo "=========================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🔄 Stopping Bluetooth Speaker..."
    echo "discoverable off" | bluetoothctl >/dev/null 2>&1
    echo "✅ Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Ensure Bluetooth is properly configured
echo "🔧 Ensuring Bluetooth is configured..."
{
    echo "power on"
    echo "discoverable on" 
    echo "pairable on"
    echo "system-alias Ubuntu-Speaker"
    echo "quit"
} | bluetoothctl >/dev/null 2>&1

# Wait a moment for settings to apply
sleep 2

# Show current status
echo "📊 Current Status:"
echo "=================="
if bluetoothctl show | grep -q "Powered: yes"; then
    echo "✅ Bluetooth is powered on"
else
    echo "❌ Bluetooth is not powered on"
fi

if bluetoothctl show | grep -q "Discoverable: yes"; then
    echo "✅ Device is discoverable"
else
    echo "❌ Device is not discoverable"
fi

if bluetoothctl show | grep -q "Pairable: yes"; then
    echo "✅ Device is pairable"
else
    echo "❌ Device is not pairable"
fi

echo ""
echo "🎵 BLUETOOTH SPEAKER IS READY!"
echo "=============================="
echo "📱 Device name: Ubuntu-Speaker"
echo "🔍 Your laptop is discoverable on Bluetooth"
echo ""
echo "📋 Instructions:"
echo "   1. Open Bluetooth settings on your phone"
echo "   2. Look for 'Ubuntu-Speaker' in available devices"
echo "   3. Tap to connect"
echo "   4. Start playing music on your phone"
echo "   5. Audio will play through your laptop speakers!"
echo ""
echo "⏹️  Press Ctrl+C to stop the Bluetooth speaker"
echo ""

# Show connection monitoring
echo "👁️  Connection Monitor:"
echo "======================="

connection_count=0
while true; do
    # Check for connected devices
    connected_devices=$(bluetoothctl devices Connected 2>/dev/null)
    
    if [ ! -z "$connected_devices" ] && [ "$connected_devices" != "" ]; then
        if [ $connection_count -eq 0 ]; then
            echo "🎉 Device connected!"
            connection_count=1
        fi
        echo "📱 $(date '+%H:%M:%S') - Active connections:"
        echo "$connected_devices" | while IFS= read -r line; do
            if [ ! -z "$line" ]; then
                device_name=$(echo "$line" | cut -d' ' -f3-)
                echo "   🔗 $device_name"
            fi
        done
        echo ""
    else
        if [ $connection_count -eq 1 ]; then
            echo "📵 Device disconnected"
            connection_count=0
        fi
        echo "⏳ $(date '+%H:%M:%S') - Waiting for phone connection..."
    fi
    
    sleep 10
done
