#!/bin/bash
# Signal CLI Docker Re-registration Script

echo "=========================================="
echo "Signal CLI Docker Re-registration Process"
echo "=========================================="

PHONE_NUMBER="+16572463906"
CONFIG_DIR="/home/ohms/signal-cli-config"

# Step 1: Ensure container is stopped
echo "1. Stopping any existing Signal container..."
docker stop signal-api 2>/dev/null
docker rm signal-api 2>/dev/null

# Step 2: Backup existing data
echo "2. Backing up existing Signal data..."
if [ -d "$CONFIG_DIR/data" ]; then
    mv "$CONFIG_DIR/data" "$CONFIG_DIR/data.backup.$(date +%Y%m%d_%H%M)"
    echo "   Backed up existing data"
fi

# Step 3: Start registration process
echo "3. Starting Signal CLI Docker for registration..."
echo "   Phone number: $PHONE_NUMBER"

# Start container in registration mode
docker run -d \
    --name signal-api \
    -p 8080:8080 \
    -v "$CONFIG_DIR:/home/.local/share/signal-cli" \
    bbernhard/signal-cli-rest-api:latest

# Wait for container to be ready
echo "4. Waiting for container to be ready..."
sleep 5

# Step 4: Register the number
echo "5. Registering phone number..."
echo "   This will send a verification code to your phone"

curl -X POST -H "Content-Type: application/json" \
    -d "{\"use_voice\": false}" \
    "http://localhost:8080/v1/register/$PHONE_NUMBER"

echo ""
echo "=========================================="
echo "IMPORTANT: Check your phone for the verification code"
echo "Then run the verify command:"
echo ""
echo "curl -X POST -H \"Content-Type: application/json\" \\"
echo "  -d '{\"pin\": \"YOUR_6_DIGIT_CODE\"}' \\"
echo "  \"http://localhost:8080/v1/register/$PHONE_NUMBER/verify/YOUR_CODE\""
echo ""
echo "Replace YOUR_6_DIGIT_CODE with the actual code (e.g., 123456)"
echo "Replace YOUR_CODE with the same code without quotes"
echo "=========================================="