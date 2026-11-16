#!/bin/bash
# =============================================================================
# Ambience Mall Gurugram - Unified Development Startup Script
#
# Starts:
#   1. Flask API on port 5001 (Mall-RL-Navigation/api.py)
#   2. Next.js Frontend on port 3000 (ambience-mall-app-ui)
# =============================================================================

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Ambience Mall Gurugram Startup ==="
echo "Project Root: $PROJECT_ROOT"

cleanup() {
  if [ -n "$BACKEND_PID" ]; then
    echo "Stopping backend (PID $BACKEND_PID)..."
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# 1. Clean up stale processes on ports 5001 and 3000
echo "Checking existing services..."
for PORT in 5001 3000; do
  PID=$(lsof -ti :$PORT || true)
  if [ -n "$PID" ]; then
    echo "Stopping existing process on port $PORT (PID $PID)..."
    kill -9 $PID 2>/dev/null || true
  fi
done

sleep 1

# 2. Start Flask Backend
echo "Starting Flask Navigation API on http://127.0.0.1:5001..."
cd "$PROJECT_ROOT/Mall-RL-Navigation"
python3 api.py > /tmp/mall_backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID), logging to /tmp/mall_backend.log"

# Wait for backend health check
echo "Waiting for backend health check..."
for i in {1..15}; do
  if curl -s http://127.0.0.1:5001/api/health > /dev/null 2>&1; then
    echo "✓ Backend is healthy on http://127.0.0.1:5001"
    break
  fi
  sleep 0.5
done

# 3. Start Next.js Frontend
echo "Starting Next.js Frontend on http://localhost:3000..."
cd "$PROJECT_ROOT/ambience-mall-app-ui"
npm run dev

