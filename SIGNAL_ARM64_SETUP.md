# Signal CLI Setup for ARM64 (Raspberry Pi) - Current Status

## Issue Summary

Signal CLI has compatibility issues on ARM64 (Raspberry Pi) architecture:
- Native binaries are compiled for x86_64
- Java versions have library compatibility issues
- ARM64 builds require compilation from source

## Current Implementation

The system is configured to send to both Telegram and Signal, but Signal will only work once properly set up. The Telegram integration continues to work normally.

## Setup Options for ARM64

### Option 1: Use signal-cli on x86_64 Machine (Recommended)

1. Set up signal-cli on an x86_64 Linux machine or VPS
2. Register the phone number there
3. Create a simple REST API wrapper
4. Point the Raspberry Pi to that API

### Option 2: Docker Container (If Docker works on your Pi)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in

# Run signal-cli-rest-api
docker run -d \
    --name signal-api \
    --restart unless-stopped \
    -p 8080:8080 \
    -v ~/signal-data:/home/.local/share/signal-cli \
    bbernhard/signal-cli-rest-api:latest

# Then update .env:
SIGNAL_API_URL=http://localhost:8080
```

### Option 3: Compile from Source

```bash
# Install dependencies
sudo apt-get install -y git gradle openjdk-17-jdk libzkgroup-java

# Clone and build
git clone https://github.com/AsamK/signal-cli.git
cd signal-cli
git checkout v0.10.11  # Last version that might work with Java 17
./gradlew build
./gradlew installDist
```

### Option 4: Use Alternative Services

- **Matrix Bridge**: Set up a Matrix server with Signal bridge
- **Webhook Services**: Use Make.com, Zapier, or IFTTT with Signal
- **Custom Bridge**: Use Python libraries like pysignal or signal-bot

## Current System Behavior

1. **Telegram**: ✅ Working normally
2. **Signal**: ⏸️ Ready but awaiting proper setup
3. **Failover**: If Signal fails, Telegram still receives messages

## Quick Test

Once Signal is set up, test with:

```bash
cd /home/ohms/OhmsAlertsReports/daily-report
python test_signal_setup.py
```

## Manual Registration (When signal-cli works)

```bash
# Register
signal-cli -u +16572463906 register

# Enter SMS code
signal-cli -u +16572463906 verify <CODE>

# Create group
signal-cli -u +16572463906 updateGroup -n "Ohms Alerts Reports" -m +16572463906

# List groups to get ID
signal-cli -u +16572463906 listGroups

# Update .env with group ID
echo "SIGNAL_GROUP_ID=group.XXXXX==" >> .env
```

## Temporary Workaround

For immediate Signal notifications, consider:

1. **Email-to-Signal**: Set up email notifications and use an email-to-Signal gateway
2. **Telegram-to-Signal**: Use a bot that forwards Telegram messages to Signal
3. **Direct API**: Use Signal's official API (requires approval)

## Next Steps

1. The system will continue sending to Telegram reliably
2. Once Signal is properly configured on compatible hardware, it will automatically start working
3. No code changes needed - just update the .env file with Signal credentials

## Support

The messaging system is designed to be fault-tolerant:
- If Signal fails, Telegram still works
- Both messengers are tried independently
- All failures are logged for debugging