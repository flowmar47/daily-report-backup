# Signal CLI Docker Registration Steps

## Current Status
Signal requires a CAPTCHA for registration. Here's the complete process:

## Step 1: Get CAPTCHA Token
1. Go to: https://signalcaptchas.org/registration/generate.html
2. Solve the captcha
3. Right-click on the "Open Signal" link
4. Copy the link (it will look like: `signalcaptcha://signal-recaptcha-v2...`)
5. Extract the token part after `signalcaptcha://`

## Step 2: Register with CAPTCHA
Once you have the captcha token, run this command:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"captcha": "YOUR_CAPTCHA_TOKEN", "use_voice": false}' \
  "http://localhost:8080/v1/register/+16572463906"
```

Replace `YOUR_CAPTCHA_TOKEN` with the token from step 1.

## Step 3: Verify with SMS Code
After registration succeeds, you'll receive an SMS code. Verify with:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"pin": "123456"}' \
  "http://localhost:8080/v1/register/+16572463906/verify/123456"
```

Replace `123456` with your actual 6-digit code.

## Step 4: Set Profile (Optional but Recommended)
```bash
curl -X PUT -H "Content-Type: application/json" \
  -d '{"name": "Ohms Alerts Bot"}' \
  "http://localhost:8080/v1/profiles/+16572463906"
```

## Step 5: Update Group Information
After registration, check groups again:
```bash
curl -X GET "http://localhost:8080/v1/groups/+16572463906"
```

## Current Docker Status
- Container Name: signal-api
- Running on: http://localhost:8080
- Config Directory: /home/ohms/signal-cli-config
- Old non-Docker signal-cli has been removed

## Testing After Registration
Test with the correct group ID:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"number": "+16572463906", "recipients": ["group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0="], "message": "Test message after re-registration"}' \
  "http://localhost:8080/v2/send"
```