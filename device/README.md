# Ubuntu Bluetooth Speaker

Turn your Ubuntu laptop into a Bluetooth A2DP speaker that can receive audio from your phone or other devices.

## Features

- Simple two-program setup
- Automatic pairing mode
- Audio routing from Bluetooth to laptop speakers
- No PIN/code required
- Clean, easy-to-use interface

## Installation

1. Make the setup script executable and run it:
```bash
chmod +x setup.sh
./setup.sh
```

2. Log out and back in (or run `newgrp bluetooth`) to apply group membership changes.

## Usage

### Two Simple Programs:

#### 1. Pairing Mode (for connecting new devices):
```bash
./bluetooth_pairing.py
```
Use this when you want to connect a new phone/device to your laptop.

#### 2. Audio Player (for already paired devices):
```bash
./bluetooth_player.py
```
Use this to receive audio from devices that are already paired.

### Step-by-Step Guide:

#### First Time Setup:
1. Run `./bluetooth_pairing.py`
2. On your phone, go to Bluetooth settings
3. Look for "Ubuntu-Speaker" and tap it
4. **No PIN required - it connects automatically!**
5. Once paired, stop the pairing program (Ctrl+C)

#### Daily Use:
1. Run `./bluetooth_player.py`
2. Your phone will automatically connect if it's nearby
3. Start playing music - audio plays through laptop speakers!

## Troubleshooting

### Check Dependencies
```bash
# Verify required packages are installed
dpkg -l | grep -E "(bluez|pulseaudio-module-bluetooth)"
```

### Check Bluetooth Status
```bash
# Check if Bluetooth is running
sudo systemctl status bluetooth

# Check if adapter is powered on
bluetoothctl show
```

### Check PulseAudio
```bash
# List audio sinks
pactl list short sinks

# List audio sources
pactl list short sources

# Check for Bluetooth modules
pactl list short modules | grep bluetooth
```

### Audio Issues
```bash
# Restart PulseAudio
pulseaudio -k && pulseaudio --start

# Check volume levels
pavucontrol
```

### View Logs
```bash
# Service logs
sudo journalctl -u bluetooth-speaker -f

# Application logs
tail -f /tmp/bluetooth_speaker.log
```

## Configuration

Edit `config.ini` to customize:
- Device name
- Pairing settings
- Audio quality
- Logging options

## Files

- `bluetooth_pairing.py` - **Pairing Mode**: Connect new devices to your laptop
- `bluetooth_player.py` - **Audio Player**: Receive audio from paired devices
- `setup.sh` - Installation script (run once)
- `config.ini` - Configuration file
- `system_check.sh` - System compatibility checker
- `backup/` - Folder containing old/backup scripts

## Requirements

- Ubuntu 18.04 or later
- Bluetooth adapter
- PulseAudio
- Python 3.6+

## Security Notes

- The service accepts pairing requests automatically
- Consider changing the pairing PIN in config.ini for better security
- The service runs with user privileges, not root

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop bluetooth-speaker
sudo systemctl disable bluetooth-speaker

# Remove service file
sudo rm /etc/systemd/system/bluetooth-speaker.service

# Remove from bluetooth group
sudo gpasswd -d $USER bluetooth

# Remove packages (optional)
sudo apt-get remove bluez pulseaudio-module-bluetooth
```
