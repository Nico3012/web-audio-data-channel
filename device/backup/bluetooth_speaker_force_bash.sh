#!/bin/bash

# Force Auto-Accept Bluetooth Speaker - Bash Version
# This version uses multiple strategies to eliminate pairing confirmations

echo "🔵 FORCE Auto-Accept Bluetooth Speaker"
echo "======================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🔄 Stopping Force Auto-Accept Bluetooth Speaker..."
    {
        echo "discoverable off"
        echo "agent off"
        echo "quit"
    } | bluetoothctl >/dev/null 2>&1
    
    # Kill any background processes
    pkill -f "bluetoothctl" 2>/dev/null || true
    
    echo "✅ Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🧹 Clearing any problematic pairings..."
bluetoothctl paired-devices 2>/dev/null | while read device; do
    if [ ! -z "$device" ] && [[ "$device" == *"Device"* ]]; then
        mac=$(echo "$device" | cut -d' ' -f2)
        if [ ! -z "$mac" ] && [[ "$mac" =~ ^[0-9A-Fa-f:]+$ ]]; then
            echo "Removing old pairing: $mac"
            echo "remove $mac" | bluetoothctl >/dev/null 2>&1
        fi
    fi
done

echo "🔧 Setting up FORCE auto-accept Bluetooth..."

# Restart Bluetooth service for clean state
echo "Restarting Bluetooth service..."
sudo systemctl restart bluetooth
sleep 3

# Configure Bluetooth step by step with error checking
echo "power on" | bluetoothctl
sleep 1

echo "agent off" | bluetoothctl
sleep 1

echo "agent NoInputNoOutput" | bluetoothctl
sleep 1

echo "default-agent" | bluetoothctl
sleep 1

echo "discoverable on" | bluetoothctl
sleep 1

echo "pairable on" | bluetoothctl
sleep 1

echo "system-alias Ubuntu-Speaker" | bluetoothctl
sleep 1

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
echo "🤖 Starting FORCE auto-accept agents..."

# Start multiple background agents for maximum coverage
{
    while true; do
        echo "agent NoInputNoOutput"
        echo "default-agent"
        sleep 30
    done
} | bluetoothctl >/dev/null 2>&1 &

AGENT1_PID=$!

# Start a second agent that specifically looks for and accepts requests
{
    expect -c '
    set timeout -1
    spawn bluetoothctl
    expect "#"
    send "agent NoInputNoOutput\r"
    expect "#"
    send "default-agent\r"
    expect "#"
    
    while {1} {
        expect {
            "*confirm*" { send "yes\r"; exp_continue }
            "*Confirm*" { send "yes\r"; exp_continue }
            "*passkey*" { send "yes\r"; exp_continue }
            "*Passkey*" { send "yes\r"; exp_continue }
            "*PIN*" { send "yes\r"; exp_continue }
            "*pin*" { send "yes\r"; exp_continue }
            "*authorize*" { send "yes\r"; exp_continue }
            "*Authorize*" { send "yes\r"; exp_continue }
            "*accept*" { send "yes\r"; exp_continue }
            "*Accept*" { send "yes\r"; exp_continue }
            "*yes/no*" { send "yes\r"; exp_continue }
            "*\[yes/no\]*" { send "yes\r"; exp_continue }
            timeout { continue }
        }
    }
    ' 2>/dev/null
} &

AGENT2_PID=$!

echo ""
echo "🎵 FORCE AUTO-ACCEPT BLUETOOTH SPEAKER READY!"
echo "=============================================="
echo "📱 Device name: Ubuntu-Speaker"
echo "🔓 FORCE Auto-accept: ENABLED"
echo "❌ NO PIN/CODE/CONFIRMATION required!"
echo ""
echo "📋 Instructions:"
echo "   1. Open Bluetooth settings on your phone"
echo "   2. Look for 'Ubuntu-Speaker'"
echo "   3. Tap to connect - ALL prompts will be auto-accepted!"
echo "   4. Start playing audio!"
echo ""
echo "⚠️  This mode FORCES acceptance of ALL pairing requests"
echo "⚠️  Multiple agents running for maximum compatibility"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Enhanced connection monitoring with auto-trust
echo "👁️  Enhanced Connection Monitor:"
echo "==============================="

connection_count=0
while true; do
    # Check for any devices (paired or unpaired)
    all_devices=$(bluetoothctl devices 2>/dev/null)
    
    if [ ! -z "$all_devices" ]; then
        echo "$all_devices" | while IFS= read -r line; do
            if [ ! -z "$line" ] && [[ "$line" == *"Device"* ]]; then
                mac=$(echo "$line" | cut -d' ' -f2)
                if [ ! -z "$mac" ] && [[ "$mac" =~ ^[0-9A-Fa-f:]+$ ]]; then
                    # Auto-trust this device
                    echo "trust $mac" | bluetoothctl >/dev/null 2>&1
                    echo "connect $mac" | bluetoothctl >/dev/null 2>&1
                fi
            fi
        done
    fi
    
    # Check for connected devices
    connected_devices=$(bluetoothctl devices Connected 2>/dev/null)
    
    if [ ! -z "$connected_devices" ] && [ "$connected_devices" != "" ]; then
        if [ $connection_count -eq 0 ]; then
            echo "🎉 Device connected successfully!"
            echo "🎵 You can now play audio from your phone!"
            connection_count=1
        fi
        echo "📱 $(date '+%H:%M:%S') - Active connections:"
        echo "$connected_devices" | while IFS= read -r line; do
            if [ ! -z "$line" ]; then
                device_name=$(echo "$line" | cut -d' ' -f3-)
                mac=$(echo "$line" | cut -d' ' -f2)
                echo "   🔗 $device_name ($mac)"
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
    
    sleep 5
done
