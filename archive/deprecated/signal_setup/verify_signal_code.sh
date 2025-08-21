#!/bin/bash
# Verify Signal Registration Code

echo "Signal CLI Docker Verification"
echo "=============================="

PHONE_NUMBER="+16572463906"

# Check if verification code was provided
if [ -z "$1" ]; then
    echo "ERROR: Please provide the 6-digit verification code"
    echo ""
    echo "Usage: ./verify_signal_code.sh 123456"
    exit 1
fi

CODE="$1"

echo "Verifying with code: $CODE"

# Verify the code
RESPONSE=$(curl -X POST -H "Content-Type: application/json" \
    -d "{\"pin\": \"$CODE\"}" \
    "http://localhost:8080/v1/register/$PHONE_NUMBER/verify/$CODE" 2>/dev/null)

echo "Response: $RESPONSE"

if [[ $RESPONSE == *"error"* ]]; then
    echo "Verification failed. Please check the code."
    exit 1
fi

echo ""
echo "=============================="
echo "✅ Verification successful!"
echo ""
echo "Setting profile name..."
curl -X PUT -H "Content-Type: application/json" \
    -d '{"name": "Ohms Alerts Bot"}' \
    "http://localhost:8080/v1/profiles/$PHONE_NUMBER"

echo ""
echo "Checking groups..."
curl -X GET "http://localhost:8080/v1/groups/$PHONE_NUMBER" | python3 -m json.tool

echo ""
echo "=============================="
echo "Registration complete! You can now test messaging with:"
echo ""
echo "curl -X POST -H \"Content-Type: application/json\" \\"
echo "  -d '{\"number\": \"$PHONE_NUMBER\", \"recipients\": [\"group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0=\"], \"message\": \"Test message\"}' \\"
echo "  \"http://localhost:8080/v2/send\""
echo "=============================="