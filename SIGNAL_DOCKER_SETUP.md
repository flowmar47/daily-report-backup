# Signal Docker Setup Instructions

## Current Status

✅ Docker is installed and running
✅ Signal CLI REST API container is running on port 8080
❌ Registration requires CAPTCHA verification

## Registration Steps

### 1. Get CAPTCHA Token

1. Open this URL in your browser:
   https://signalcaptchas.org/registration/generate.html

2. Solve the CAPTCHA puzzle

3. After solving, you'll see an "Open Signal" button
   - Right-click on it
   - Select "Copy Link Address"
   - The link will look like: `signalcaptcha://signal-recaptcha...`

4. Extract the token part after `signalcaptcha://`

### 2. Register with CAPTCHA

Run this command with your CAPTCHA token:

```bash
curl -X POST http://localhost:8080/v1/register/+16572463906 \
  -H "Content-Type: application/json" \
  -d '{"captcha": "YOUR_CAPTCHA_TOKEN_HERE"}'
```

### 3. Verify SMS Code

When you receive the SMS code, verify it:

```bash
curl -X POST http://localhost:8080/v1/register/+16572463906/verify/YOUR_CODE
```

### 4. Create Group

Create the Ohms Alerts Reports group:

```bash
curl -X POST http://localhost:8080/v1/groups/+16572463906 \
  -H "Content-Type: application/json" \
  -d '{"name": "Ohms Alerts Reports", "members": ["+16572463906"]}'
```

### 5. Get Group ID

List groups to get the ID:

```bash
curl http://localhost:8080/v1/groups/+16572463906
```

### 6. Update Configuration

Add to `/home/ohms/OhmsAlertsReports/daily-report/.env`:

```
SIGNAL_PHONE_NUMBER=+16572463906
SIGNAL_GROUP_ID=<group_id_from_step_5>
SIGNAL_API_URL=http://localhost:8080
```

### 7. Test Sending

Test the integration:

```bash
cd /home/ohms/OhmsAlertsReports/daily-report
python test_signal_setup.py
```

## Docker Container Management

### Check Status
```bash
sudo docker ps | grep signal-api
```

### View Logs
```bash
sudo docker logs -f signal-api
```

### Restart Container
```bash
sudo docker restart signal-api
```

### Stop Container
```bash
sudo docker stop signal-api
```

## API Documentation

The Signal REST API documentation is available at:
http://localhost:8080/v1/api-docs

## Troubleshooting

### Container not starting
```bash
# Check logs
sudo docker logs signal-api

# Remove and recreate
sudo docker stop signal-api
sudo docker rm signal-api
sudo docker run -d --name signal-api --restart unless-stopped -p 8080:8080 -v ~/signal-api-data:/home/.local/share/signal-cli bbernhard/signal-cli-rest-api:latest
```

### API not responding
```bash
# Check if port is open
sudo netstat -tlnp | grep 8080

# Test API
curl http://localhost:8080/v1/about
```

### Registration issues
- Make sure to get a fresh CAPTCHA token
- Ensure phone number can receive SMS
- Check Docker logs for detailed errors

## Next Steps

Once registered and group created:
1. The system will automatically send to both Telegram and Signal
2. Messages are sent concurrently - if one fails, the other still works
3. All activity is logged in `/home/ohms/OhmsAlertsReports/daily-report/logs/`