# Quick Bluetooth Speaker Setup Commands

# 1. First, clear any old pairings
bluetoothctl paired-devices
# For each device listed, run: bluetoothctl remove [MAC-ADDRESS]

# 2. Set up Bluetooth
bluetoothctl power on
bluetoothctl agent KeyboardDisplay  
bluetoothctl default-agent
bluetoothctl discoverable on
bluetoothctl pairable on
bluetoothctl system-alias Ubuntu-Speaker

# 3. Check status
bluetoothctl show

# 4. Start interactive mode for pairing
bluetoothctl
# In bluetoothctl, when phone connects:
# - Type "yes" for pairing confirmation
# - Type "trust [MAC-ADDRESS]" after successful pairing
# - Type "quit" to exit
