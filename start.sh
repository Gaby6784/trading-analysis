#!/bin/bash
# Start script for Railway deployment

echo "🚀 Starting Trading Analysis Platform..."

# Check if scheduler should run
if [ "$SCHEDULER_ENABLED" = "true" ]; then
    echo "⏰ Starting scheduler in background..."
    python3 scheduler.py &
    SCHEDULER_PID=$!
    echo "   Scheduler PID: $SCHEDULER_PID"
fi

# Start Flask app
echo "🌐 Starting Flask API..."
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

# Cleanup on exit
trap "kill $SCHEDULER_PID 2>/dev/null" EXIT
