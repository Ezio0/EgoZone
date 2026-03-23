#!/bin/bash
# EgoZone service stop script

echo "🛑 Stopping EgoZone service..."

# Check if PID file exists
if [ -f "egozone_server.pid" ]; then
    SERVER_PID=$(cat egozone_server.pid)

    # Check if process is still running
    if ps -p $SERVER_PID > /dev/null; then
        echo "🔄 Sending termination signal to PID: $SERVER_PID"
        kill $SERVER_PID

        # Wait for process to end
        sleep 2

        # If process is still running, force terminate
        if ps -p $SERVER_PID > /dev/null; then
            echo "💥 Force terminating process PID: $SERVER_PID"
            kill -9 $SERVER_PID
        fi

        # Remove PID file
        rm egozone_server.pid
        echo "✅ Service stopped"
    else
        echo "⚠️  Process PID $SERVER_PID does not exist"
        rm egozone_server.pid
    fi
else
    echo "🔍 PID file not found, searching for related processes..."
    PIDS=$(ps aux | grep -E "uvicorn.*main" | grep -v grep | awk '{print $2}')

    if [ ! -z "$PIDS" ]; then
        echo "🔄 Stopping found EgoZone processes: $PIDS"
        kill $PIDS 2>/dev/null || kill -9 $PIDS 2>/dev/null
        echo "✅ Service stopped"
    else
        echo "✅ No running EgoZone service found"
    fi
fi