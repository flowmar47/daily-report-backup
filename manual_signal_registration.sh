#!/bin/bash

# Manual Signal Registration Script
# Phone: +16572463906

echo "=== Manual Signal Registration ==="
echo ""
echo "Step 1: Get CAPTCHA token"
echo "1. Visit: https://signalcaptchas.org/registration/generate.html"
echo "2. Solve the CAPTCHA"
echo "3. Copy the verification link"
echo ""
read -p "Enter CAPTCHA token (or full URL): " CAPTCHA_INPUT

# Extract token from URL if needed
if [[ $CAPTCHA_INPUT == signalcaptcha://* ]]; then
    CAPTCHA_TOKEN="${CAPTCHA_INPUT#signalcaptcha://}"
else
    CAPTCHA_TOKEN="$CAPTCHA_INPUT"
fi

echo ""
echo "Step 2: Registering with Signal..."
RESPONSE=$(curl -s -X POST http://localhost:8080/v1/register/+16572463906 \
  -H "Content-Type: application/json" \
  -d "{\"captcha\": \"$CAPTCHA_TOKEN\"}")

echo "Response: $RESPONSE"

if [[ $RESPONSE == *"error"* ]]; then
    echo "Registration failed. Please check the CAPTCHA token."
    exit 1
fi

echo ""
echo "Step 3: SMS Verification"
echo "Check your phone for SMS verification code..."
read -p "Enter SMS code: " SMS_CODE

echo ""
echo "Verifying SMS code..."
VERIFY_RESPONSE=$(curl -s -X POST http://localhost:8080/v1/register/+16572463906/verify/$SMS_CODE)

echo "Response: $VERIFY_RESPONSE"

if [[ $VERIFY_RESPONSE == *"error"* ]]; then
    echo "Verification failed. Please check the SMS code."
    exit 1
fi

echo ""
echo "Step 4: Creating group..."
GROUP_RESPONSE=$(curl -s -X POST http://localhost:8080/v1/groups/+16572463906 \
  -H "Content-Type: application/json" \
  -d '{"name": "Ohms Alerts Reports", "members": ["+16572463906"]}')

echo "Group creation response: $GROUP_RESPONSE"

echo ""
echo "Step 5: Getting group ID..."
GROUPS=$(curl -s http://localhost:8080/v1/groups/+16572463906 | jq -r '.[] | select(.name=="Ohms Alerts Reports") | .id')

if [ -n "$GROUPS" ]; then
    echo "Group ID: $GROUPS"
    echo ""
    echo "Updating .env file..."
    sed -i "s/SIGNAL_GROUP_ID=.*/SIGNAL_GROUP_ID=$GROUPS/" .env
    echo "✅ Registration complete!"
else
    echo "Failed to get group ID"
fi