#!/bin/bash

# Simple Force Auto-Accept Bluetooth Speaker
# Uses the most basic approach to avoid pairing confirmations

echo "🔵 Simple Force Auto-Accept Bluetooth Speaker"
echo "============================================="
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

# Kill any existing bluetoothctl processes
pkill -f bluetoothctl 2>/dev/null || true
sleep 2

echo "🧹 Clearing old pairings..."
bluetoothctl paired-devices | while read device; do
    if [[ "$device" == *"Device"* ]]; then
        mac=$(echo "$device" | cut -d' ' -f2)
        echo "remove $mac" | bluetoothctl >/dev/null 2>&1
    fi
done

echo "🔧 Configuring Bluetooth for zero-confirmation pairing..."

# Configure Bluetooth with the most permissive settings
bluetoothctl <<EOF
power on
agent off
agent NoInputNoOutput
default-agent
discoverable on
pairable on
system-alias Ubuntu-Speaker
quit
EOF

sleep 2

# Check status
echo "📊 Current Status:"
echo "=================="
bluetoothctl show | grep -E "(Powered|Discoverable|Pairable|Alias)" | while read line; do
    if echo "$line" | grep -q "yes\|Ubuntu-Speaker"; then
        echo "✅ $line"
    else
        echo "❌ $line"
    fi
done

echo ""
echo "🎵 SIMPLE FORCE AUTO-ACCEPT READY!"
echo "=================================="
echo "📱 Device name: Ubuntu-Speaker"
echo "🔓 Zero-confirmation mode enabled"
echo ""
echo "📋 Try connecting from your phone now:"
echo "   1. Open Bluetooth settings on your phone"
echo "   2. Look for 'Ubuntu-Speaker'"
echo "   3. Tap to connect"
echo "   4. It should connect without ANY prompts!"
echo ""
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Simple monitoring loop
echo "👁️  Connection Monitor:"
echo "======================="

while true; do
    connected=$(bluetoothctl devices Connected 2>/dev/null)
    
    if [ ! -z "$connected" ] && [ "$connected" != "" ]; then
        echo "🎉 $(date '+%H:%M:%S') - Device connected!"
        echo "🎵 You can now play audio!"
        echo "$connected" | while read line; do
            if [ ! -z "$line" ]; then
                device_name=$(echo "$line" | cut -d' ' -f3-)
                mac=$(echo "$line" | cut -d' ' -f2)
                echo "   🔗 $device_name ($mac)"
                # Auto-trust for future connections
                echo "trust $mac" | bluetoothctl >/dev/null 2>&1
            fi
        done
        echo ""
    else
        echo "⏳ $(date '+%H:%M:%S') - Waiting for connection..."
    fi
    
    sleep 8
done
