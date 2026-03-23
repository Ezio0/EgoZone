#!/bin/bash
# EgoZone service restart script

echo "🔄 Restarting EgoZone service..."

# First stop the service
echo "🛑 Stopping existing service..."
./stop_service.sh

# Wait for service to fully stop
sleep 3

# Start the service
echo "🚀 Starting new service..."
./start_service.sh