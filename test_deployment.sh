#!/bin/bash

echo "🧪 Testing SousSpeed Application"
echo "================================"

# Set environment for testing
export FLASK_ENV=production
export PORT=8080

# Start the app in background
python3 app.py &
APP_PID=$!

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 5

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -s http://localhost:8080/api/health > /dev/null; then
    echo "✅ Health check passed"
    
    # Test calculation endpoint
    echo "🧮 Testing calculation endpoint..."
    RESULT=$(curl -s -X POST http://localhost:8080/api/calculate \
        -H "Content-Type: application/json" \
        -d '{"protein_type": "beef", "thickness_inches": 1.5, "target_temp_celsius": 54, "doneness": "medium-rare", "weight_kg": 0.8}')
    
    if echo "$RESULT" | grep -q "success.*true"; then
        echo "✅ Calculation endpoint working"
        echo "📊 Sample result: Time savings $(echo "$RESULT" | grep -o 'time_savings_percent[^,]*' | cut -d: -f2)%"
    else
        echo "❌ Calculation endpoint failed"
        echo "$RESULT"
    fi
    
    # Test main page
    echo "🌐 Testing main page..."
    if curl -s http://localhost:8080/ | grep -q "SousSpeed"; then
        echo "✅ Main page accessible"
    else
        echo "❌ Main page not accessible"
    fi
    
else
    echo "❌ Health check failed"
    echo "📋 Application logs:"
    jobs -p | xargs -I {} ps -p {} -o pid,cmd
fi

# Cleanup
echo "🧹 Cleaning up..."
kill $APP_PID 2>/dev/null || true
wait $APP_PID 2>/dev/null || true

echo "✨ Test complete!"
