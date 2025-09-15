#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting deployment..."

# 1. Go to the project directory (adjust if needed)
# cd /path/to/your/project

# 2. Pull the latest code
echo "🔄 Pulling latest code from git..."
git pull origin main

# 3. Install backend dependencies
echo "🐍 Installing backend dependencies..."
python3 -m pip install -r backend/requirements.txt

# 4. Install frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install --prefix frontend

# 5. Build the frontend
echo "🎨 Building frontend application..."
npm run --prefix frontend build

# 6. Restart the backend service
# The command depends on how you run the service in production.
# Using systemd is a common and robust way.
echo "🔄 Restarting backend service..."
# sudo systemctl restart tothemoon.service
echo "(Skipping systemd restart for now. You would uncomment the line above on a real server)"

# As a fallback for local testing, we can kill the old process and start a new one.
# This is NOT for production.
if pgrep -f "uvicorn backend.app.main:app"; then
    pkill -f "uvicorn backend.app.main:app"
    echo "Killed old uvicorn process."
fi
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & 

echo "Backend started in background for testing."

# 7. Health Check
echo "🩺 Performing health check..."
sleep 10 # Wait for the server to start

if curl -f http://localhost:8000/health; then
    echo "✅ Health check passed!"
    echo "🎉 Deployment successful!"
else
    echo "❌ Health check failed! Deployment might have failed." >&2
    exit 1
fi
