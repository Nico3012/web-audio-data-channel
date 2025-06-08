#!/usr/bin/env python3
"""
Test script to verify Bluetooth cleanup functionality
"""

print("🧪 Testing Bluetooth cleanup functionality...")
print("=" * 50)

# Import modules
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bluetooth_player import BluetoothPlayer
from bluetooth_pairing import BluetoothPairing

# Test player cleanup
print("\n1. Testing BluetoothPlayer cleanup:")
player = BluetoothPlayer()
player.cleanup_bluetooth()

print("\n2. Testing BluetoothPairing cleanup:")
pairing = BluetoothPairing()
pairing.cleanup_bluetooth()

print("\n✅ Cleanup test completed!")
print("🔍 Check if Bluetooth audio stopped working from your phone")
