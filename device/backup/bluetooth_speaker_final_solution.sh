#!/bin/bash

# Final Working Bluetooth Speaker - Manual Agent Setup
# This script provides the most reliable pairing experience

echo "🔵 Ubuntu Bluetooth Speaker - Final Solution"
echo "============================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🔄 Cleaning up..."
    bluetoothctl discoverable off 2>/dev/null
    echo "✅ Bluetooth Speaker stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Clear any existing pairings that might cause conflicts
echo "🧹 Clearing problematic pairings..."
bluetoothctl paired-devices 2>/dev/null | while read device; do
    if [[ "$device" == *"Device"* ]]; then
        mac=$(echo "$device" | cut -d' ' -f2)
        if [[ "$mac" =~ ^[0-9A-Fa-f:]{17}$ ]]; then
            echo "Removing: $mac"
            bluetoothctl remove "$mac" 2>/dev/null
        fi
    fi
done

echo "🔧 Configuring Bluetooth..."

# Ensure Bluetooth is powered and configured
bluetoothctl power on
sleep 1
bluetoothctl discoverable on
sleep 1 
bluetoothctl pairable on
sleep 1

# Check status
echo ""
echo "📊 Current Status:"
echo "=================="
bluetoothctl show | grep -E "(Alias|Powered|Discoverable|Pairable)" | while read line; do
    if echo "$line" | grep -q "yes\|Ubuntu-Speaker"; then
        echo "✅ $line"
    else
        echo "❌ $line"
    fi
done

echo ""
echo "🎵 BLUETOOTH SPEAKER READY!"
echo "=========================="
echo "📱 Device name: Ubuntu-Speaker"
echo "🔍 Your laptop is now discoverable"
echo ""
echo "📋 IMPORTANT - Pairing Instructions:"
echo "===================================="
echo "1. Open Bluetooth settings on your phone"
echo "2. Look for 'Ubuntu-Speaker' and tap it"
echo "3. ⚠️  WHEN YOUR PHONE SHOWS A PAIRING CODE:"
echo "   - DON'T enter anything on your phone yet"
echo "   - Watch this terminal window"
echo "   - I'll tell you exactly what to do"
echo ""
echo "🎧 Once paired, audio will play through laptop speakers"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Start monitoring for pairing requests
echo "👁️  Monitoring for connections and pairing requests..."
echo "====================================================="

last_connected=""
pairing_active=false

while true; do
    # Check for connected devices
    connected=$(bluetoothctl devices Connected 2>/dev/null)
    
    if [ ! -z "$connected" ] && [ "$connected" != "$last_connected" ]; then
        echo ""
        echo "🎉 $(date '+%H:%M:%S') - Device connected successfully!"
        echo "🎵 You can now play audio from your phone!"
        echo "$connected" | while read line; do
            if [ ! -z "$line" ]; then
                device_name=$(echo "$line" | cut -d' ' -f3-)
                mac=$(echo "$line" | cut -d' ' -f2)
                echo "   ✅ Connected: $device_name ($mac)"
                # Auto-trust for future connections
                bluetoothctl trust "$mac" 2>/dev/null
            fi
        done
        echo ""
        last_connected="$connected"
        pairing_active=false
    elif [ -z "$connected" ] && [ ! -z "$last_connected" ]; then
        echo "📵 $(date '+%H:%M:%S') - Device disconnected"
        last_connected=""
        pairing_active=false
    fi
    
    # Check for pairing requests by looking at bluetoothctl output
    if [ -z "$connected" ] && [ "$pairing_active" = false ]; then
        # Check if there are any devices trying to pair
        devices=$(bluetoothctl devices 2>/dev/null)
        
        if [ ! -z "$devices" ]; then
            echo "$devices" | while read device_line; do
                if [[ "$device_line" == *"Device"* ]]; then
                    mac=$(echo "$device_line" | cut -d' ' -f2)
                    device_name=$(echo "$device_line" | cut -d' ' -f3-)
                    
                    # Check if this device is trying to connect
                    info=$(bluetoothctl info "$mac" 2>/dev/null)
                    if echo "$info" | grep -q "Connected: no" && echo "$info" | grep -q "Paired: no"; then
                        echo ""
                        echo "🔔 PAIRING REQUEST DETECTED!"
                        echo "=========================="
                        echo "📱 Device: $device_name ($mac)"
                        echo ""
                        echo "⚠️  IF YOUR PHONE IS ASKING FOR PAIRING CONFIRMATION:"
                        echo "   1. Check if it shows a 6-digit code"
                        echo "   2. If YES, tap 'Accept' or 'Pair' on your phone"
                        echo "   3. If NO, just wait - it should connect automatically"
                        echo ""
                        
                        # Auto-trust the device
                        bluetoothctl trust "$mac" 2>/dev/null
                        pairing_active=true
                    fi
                fi
            done
        fi
    fi
    
    if [ -z "$connected" ] && [ "$pairing_active" = false ]; then
        echo "⏳ $(date '+%H:%M:%S') - Waiting for phone connection..."
    fi
    
    sleep 3
done
