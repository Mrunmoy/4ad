#!/usr/bin/env python3
"""Run the Four Against Darkness web server."""
from src.app import app, socketio

if __name__ == '__main__':
    print("=" * 50)
    print("Four Against Darkness - Web Server")
    print("=" * 50)
    print("\nServer starting on http://0.0.0.0:5000")
    print("Access from LAN using your machine's IP address")
    print("\nPress Ctrl+C to stop\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
