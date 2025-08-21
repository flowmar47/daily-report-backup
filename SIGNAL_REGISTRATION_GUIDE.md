# Signal Registration Guide

## ✅ Status: Docker Setup Complete

The Signal CLI REST API is now running successfully in Docker on your Raspberry Pi!

```
🐳 Docker Container: ✅ Running
🌐 API Connectivity: ✅ Working (v0.92)
📱 Registration: ⏳ Needs CAPTCHA verification
```

## 📱 Complete Registration Process

### Step 1: Run the Registration Helper

```bash
cd /home/ohms/OhmsAlertsReports/daily-report
python register_signal_captcha.py
```

### Step 2: Solve CAPTCHA

The script will show you:
1. A URL to visit: https://signalcaptchas.org/registration/generate.html
2. Instructions to solve the CAPTCHA
3. How to copy the verification link

### Step 3: SMS Verification

After CAPTCHA, you'll receive an SMS code to verify.

### Step 4: Group Creation

The script will automatically:
- Create "Ohms Alerts Reports" group
- Get the group ID
- Save configuration to .env
- Send a test message

## 🔧 Manual Commands (Alternative)

If you prefer manual setup:

```bash
# 1. Get CAPTCHA token from https://signalcaptchas.org/registration/generate.html
curl -X POST http://localhost:8080/v1/register/+16572463906 \
  -H "Content-Type: application/json" \
  -d '{"captcha": "YOUR_CAPTCHA_TOKEN"}'

# 2. Verify SMS code
curl -X POST http://localhost:8080/v1/register/+16572463906/verify/SMS_CODE

# 3. Create group
curl -X POST http://localhost:8080/v1/groups/+16572463906 \
  -H "Content-Type: application/json" \
  -d '{"name": "Ohms Alerts Reports", "members": ["+16572463906"]}'

# 4. List groups to get ID
curl http://localhost:8080/v1/groups/+16572463906
```

## 📝 What Happens After Registration

Once registered, your system will:

1. **Send to Both Platforms**: Daily reports go to both Telegram and Signal
2. **Concurrent Delivery**: Messages sent simultaneously at 8 AM PST
3. **Fault Tolerance**: If one platform fails, the other still works
4. **Logging**: All delivery attempts logged for debugging

## 🧪 Testing the Setup

Check status anytime with:
```bash
python check_signal_status.py
```

Test message sending:
```bash
python -c "
from signal_messenger import SignalMessenger
messenger = SignalMessenger()
print('Connection test:', messenger.test_connection())
print('Message test:', messenger.send_message('Test from CLI'))
"
```

## 📊 Integration Benefits

- **Redundancy**: Two delivery channels ensure alerts reach you
- **Flexibility**: Can disable either platform if needed
- **Logging**: Full audit trail of message delivery
- **ARM64 Compatible**: Docker solution works on Raspberry Pi

## 🔄 Service Integration

The system automatically uses both messengers:

```python
# In main.py
await self.send_report_to_messengers(report)
# ↓
# Sends to Telegram: ✅
# Sends to Signal:   ✅ (after registration)
```

## 🚨 Troubleshooting

### Container Issues
```bash
sudo docker logs signal-api
sudo docker restart signal-api
```

### API Issues
```bash
curl http://localhost:8080/v1/about
```

### Registration Issues
- Use fresh CAPTCHA tokens
- Check phone can receive SMS
- Verify exact CAPTCHA link format

## 🎯 Ready to Complete?

Run this command to start registration:

```bash
python register_signal_captcha.py
```

The script will guide you through each step with clear instructions!