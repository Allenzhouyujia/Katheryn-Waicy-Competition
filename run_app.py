import os
from dotenv import load_dotenv

# Load environment variables from .env file
# Make sure .env file exists with your API keys
# See .env.example for template
load_dotenv()

# 启动应用
import uvicorn
from app import app

import sys
import socket

def is_port_available(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except:
        return False

# Find available port
port = 8000
found_port = None
for i in range(10):
    if is_port_available(port):
        found_port = port
        break
    print(f"Port {port} is in use, trying port {port + 1}...")
    port += 1

if found_port is None:
    print(f"Could not find available port (8000-8009). Please close the process using the port.")
    sys.exit(1)

print(f"Starting AI Mental Health Assistant...")
print(f"Access: http://localhost:{found_port}")
print("Press Ctrl+C to stop the server")
print("=" * 50)

try:
    uvicorn.run(app, host="0.0.0.0", port=found_port, log_level="info")
except KeyboardInterrupt:
    print("\nServer stopped")
