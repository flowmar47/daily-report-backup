#!/bin/bash
# Complete Signal Registration with CAPTCHA

echo "Signal CLI Docker Registration with CAPTCHA"
echo "=========================================="

PHONE_NUMBER="+16572463906"

# Check if captcha token was provided
if [ -z "$1" ]; then
    echo "ERROR: Please provide the captcha token as an argument"
    echo ""
    echo "Usage: ./complete_signal_registration.sh YOUR_CAPTCHA_TOKEN"
    echo ""
    echo "To get the captcha token:"
    echo "1. Go to: https://signalcaptchas.org/registration/generate.html"
    echo "2. Solve the captcha"
    echo "3. Right-click 'Open Signal' and copy link"
    echo "4. Extract token after 'signalcaptcha://'"
    exit 1
fi

CAPTCHA_TOKEN="$1"

echo "Registering with captcha token..."
RESPONSE=$(curl -X POST -H "Content-Type: application/json" \
    -d "{\"captcha\": \"$CAPTCHA_TOKEN\", \"use_voice\": false}" \
    "http://localhost:8080/v1/register/$PHONE_NUMBER" 2>/dev/null)

echo "Response: $RESPONSE"

if [[ $RESPONSE == *"error"* ]]; then
    echo "Registration failed. Please check the captcha token."
    exit 1
fi

echo ""
echo "=========================================="
echo "Registration request sent!"
echo "Check your phone for the verification code."
echo ""
echo "Once you receive the code, verify with:"
echo "./verify_signal_code.sh YOUR_6_DIGIT_CODE"
echo "=========================================="