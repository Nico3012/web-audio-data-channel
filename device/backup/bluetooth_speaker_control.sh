#!/bin/bash

case "$1" in
    start)
        echo "Starting Bluetooth Speaker service..."
        sudo systemctl start bluetooth-speaker
        sudo systemctl status bluetooth-speaker
        ;;
    stop)
        echo "Stopping Bluetooth Speaker service..."
        sudo systemctl stop bluetooth-speaker
        ;;
    restart)
        echo "Restarting Bluetooth Speaker service..."
        sudo systemctl restart bluetooth-speaker
        sudo systemctl status bluetooth-speaker
        ;;
    status)
        sudo systemctl status bluetooth-speaker
        ;;
    enable)
        echo "Enabling Bluetooth Speaker service to start on boot..."
        sudo systemctl enable bluetooth-speaker
        ;;
    disable)
        echo "Disabling Bluetooth Speaker service from starting on boot..."
        sudo systemctl disable bluetooth-speaker
        ;;
    logs)
        sudo journalctl -u bluetooth-speaker -f
        ;;
    manual)
        echo "Running Bluetooth Speaker manually..."
        ./bluetooth_speaker_final.sh
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|logs|manual}"
        echo
        echo "Commands:"
        echo "  start   - Start the Bluetooth speaker service"
        echo "  stop    - Stop the Bluetooth speaker service"
        echo "  restart - Restart the Bluetooth speaker service"
        echo "  status  - Show service status"
        echo "  enable  - Enable service to start on boot"
        echo "  disable - Disable service from starting on boot"
        echo "  logs    - Show service logs (live)"
        echo "  manual  - Run manually in terminal"
        exit 1
        ;;
esac
