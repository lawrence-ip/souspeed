#!/bin/bash
# Startup script for SousSpeed application

echo "🚀 Starting SousSpeed Application..."

# Check if Python dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Start Python API server in background
echo "🔬 Starting Thermodynamic Calculator API..."
python3 api_server.py &
API_PID=$!

# Wait for API to start
sleep 3

# Check if API is running
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Thermodynamic API is running on port 5000"
else
    echo "⚠️  Warning: Thermodynamic API failed to start, using JavaScript fallback"
fi

# Start web server
echo "🌐 Starting Web Server..."
python3 -m http.server 8000 &
WEB_PID=$!

echo "🍳 SousSpeed is ready!"
echo "   Web Interface: http://localhost:8000"
echo "   API Server: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down SousSpeed..."
    kill $API_PID 2>/dev/null
    kill $WEB_PID 2>/dev/null
    echo "👋 Goodbye!"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT

# Wait for processes
wait
