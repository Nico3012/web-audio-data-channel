#!/bin/bash

# Auto-Accept Bluetooth Speaker Script
# Automatically accepts all pairing requests without prompts

echo "🔵 Ubuntu Bluetooth Speaker - Auto-Accept Mode"
echo "=============================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🔄 Stopping Bluetooth Speaker..."
    {
        echo "discoverable off"
        echo "quit"
    } | bluetoothctl >/dev/null 2>&1
    echo "✅ Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Clear any existing pairings that might be causing issues
echo "🧹 Clearing any problematic pairings..."
bluetoothctl paired-devices 2>/dev/null | while read device; do
    if [ ! -z "$device" ]; then
        mac=$(echo "$device" | cut -d' ' -f2)
        if [ ! -z "$mac" ] && [[ "$mac" =~ ^[0-9A-Fa-f:]+$ ]]; then
            echo "Removing old pairing: $mac"
            echo "remove $mac" | bluetoothctl >/dev/null 2>&1
        fi
    fi
done

echo "🔧 Configuring Bluetooth for auto-accept..."

# Configure Bluetooth with auto-accept agent
{
    echo "power on"
    sleep 1
    echo "agent NoInputNoOutput"
    sleep 1
    echo "default-agent" 
    sleep 1
    echo "discoverable on"
    sleep 1
    echo "pairable on"
    sleep 1
    echo "system-alias Ubuntu-Speaker"
    sleep 1
} | bluetoothctl >/dev/null 2>&1

# Verify configuration
echo "📊 Bluetooth Status:"
echo "=================="
status=$(bluetoothctl show 2>/dev/null)

if echo "$status" | grep -q "Powered: yes"; then
    echo "✅ Bluetooth is powered on"
else
    echo "❌ Bluetooth is not powered on"
fi

if echo "$status" | grep -q "Discoverable: yes"; then
    echo "✅ Device is discoverable"
else
    echo "❌ Device is not discoverable"
fi

if echo "$status" | grep -q "Pairable: yes"; then
    echo "✅ Device is pairable"
else
    echo "❌ Device is not pairable"
fi

if echo "$status" | grep -q "Ubuntu-Speaker"; then
    echo "✅ Device name set to Ubuntu-Speaker"
else
    echo "⚠️  Device name may not be set correctly"
fi

echo ""
echo "🤖 Starting auto-accept agent..."

# Start bluetoothctl with auto-accept agent in background
{
    echo "agent NoInputNoOutput"
    echo "default-agent"
    # Keep it running to handle pairing requests
    while true; do
        sleep 30
    done
} | bluetoothctl >/dev/null 2>&1 &

AGENT_PID=$!

echo ""
echo "🎵 BLUETOOTH SPEAKER READY - AUTO-ACCEPT MODE!"
echo "=============================================="
echo "📱 Device name: Ubuntu-Speaker"
echo "🔓 Auto-accept: ENABLED (no PIN required)"
echo ""
echo "📋 Instructions:"
echo "   1. Open Bluetooth settings on your phone"
echo "   2. Look for 'Ubuntu-Speaker'"
echo "   3. Tap to connect - it will pair automatically!"
echo "   4. Start playing music!"
echo ""
echo "⚠️  Note: This mode automatically accepts ALL pairing requests"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Monitor connections
echo "👁️  Connection Monitor:"
echo "======================="

connection_count=0
while true; do
    # Check for connected devices
    connected_devices=$(bluetoothctl devices Connected 2>/dev/null)
    
    if [ ! -z "$connected_devices" ] && [ "$connected_devices" != "" ]; then
        if [ $connection_count -eq 0 ]; then
            echo "🎉 Device connected successfully!"
            echo "🎵 You can now play music from your phone"
            connection_count=1
        fi
        echo "📱 $(date '+%H:%M:%S') - Active connections:"
        echo "$connected_devices" | while IFS= read -r line; do
            if [ ! -z "$line" ]; then
                device_name=$(echo "$line" | cut -d' ' -f3-)
                mac=$(echo "$line" | cut -d' ' -f2)
                echo "   🔗 $device_name ($mac)"
                
                # Auto-trust the device for future connections
                echo "trust $mac" | bluetoothctl >/dev/null 2>&1
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
