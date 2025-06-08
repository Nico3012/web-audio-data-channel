#!/bin/bash

# Simple Bluetooth Speaker with Manual Pairing
# This version guides you through the pairing process step by step

echo "🔵 Ubuntu Bluetooth Speaker - Manual Pairing Mode"
echo "================================================="
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
bluetoothctl paired-devices | while read device; do
    if [ ! -z "$device" ]; then
        mac=$(echo "$device" | cut -d' ' -f2)
        echo "Removing old pairing: $mac"
        echo "remove $mac" | bluetoothctl >/dev/null 2>&1
    fi
done

# Configure Bluetooth step by step
echo "🔧 Configuring Bluetooth..."

# Step 1: Power on
echo "power on" | bluetoothctl >/dev/null 2>&1
sleep 1

# Step 2: Set up agent
echo "agent KeyboardDisplay" | bluetoothctl >/dev/null 2>&1
sleep 1
echo "default-agent" | bluetoothctl >/dev/null 2>&1
sleep 1

# Step 3: Make discoverable and pairable
echo "discoverable on" | bluetoothctl >/dev/null 2>&1
sleep 1
echo "pairable on" | bluetoothctl >/dev/null 2>&1
sleep 1

# Step 4: Set device name
echo "system-alias Ubuntu-Speaker" | bluetoothctl >/dev/null 2>&1
sleep 1

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
echo "🎵 BLUETOOTH SPEAKER READY FOR PAIRING!"
echo "======================================="
echo "📱 Device name: Ubuntu-Speaker"
echo "🔑 PIN code: 0000 (if asked)"
echo ""
echo "📋 PAIRING INSTRUCTIONS:"
echo "========================"
echo "1. Open Bluetooth settings on your phone"
echo "2. Look for 'Ubuntu-Speaker' and tap it"
echo "3. If asked for a PIN, enter: 0000"
echo "4. If you see a pairing request on this terminal, type 'yes'"
echo "5. Start playing music!"
echo ""
echo "⚠️  IMPORTANT: Watch this terminal for pairing requests!"
echo "📺 Keep this window visible during pairing"
echo ""
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Start interactive bluetoothctl for manual pairing
echo "👁️  Starting interactive pairing mode..."
echo "========================================="
echo "💡 When your phone tries to connect, you'll see pairing requests here"
echo "💡 Type 'yes' and press Enter when prompted"
echo "💡 Type 'trust [MAC-ADDRESS]' after successful pairing"
echo ""

# Start bluetoothctl in interactive mode for pairing
bluetoothctl
