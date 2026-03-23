#!/bin/bash
# EgoZone local development service startup script

echo "🚀 Starting EgoZone local development service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found, please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if a service is already running on the port
if lsof -ti:8000; then
    echo "⚠️  Port 8000 is already in use, attempting to stop existing service..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No process found using port 8000"
fi

# Activate virtual environment and start service
echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "⚡ Starting FastAPI service..."
# Start service and redirect output to log file
nohup uvicorn main:app --host 127.0.0.1 --port 8000 --reload > service_output.log 2>&1 &

SERVER_PID=$!
echo "✅ Service started, PID: $SERVER_PID"
echo "🌐 Access URL: http://127.0.0.1:8000"

# Write PID to file for future service stop
echo $SERVER_PID > egozone_server.pid

echo "📝 Log file: service_output.log"
echo "📌 To stop the service, run: ./stop_service.sh"