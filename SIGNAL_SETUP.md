# Signal CLI Setup for Ohms Alerts Reports

This guide explains how to set up Signal CLI to send the daily financial reports to a Signal group in addition to Telegram.

## Prerequisites

- Raspberry Pi with Debian/Raspbian OS
- Phone number: +16572463906
- Java runtime (will be installed automatically)

## Installation Steps

### 1. Install Signal CLI

Run the installation script:

```bash
cd /home/ohms/OhmsAlertsReports/daily-report
./setup_signal_cli.sh
```

This will:
- Download Signal CLI v0.13.4
- Install Java if not present
- Create necessary symlinks
- Install dependencies

### 2. Register Phone Number

Run the registration script:

```bash
./run_signal_registration.sh
# OR
python register_signal.py
```

Follow these steps:
1. The script will send an SMS verification code to +16572463906
2. Enter the 6-digit code when prompted
3. The script will verify the number with Signal

### 3. Create Signal Group

After registration:
1. The script will create a group called "Ohms Alerts Reports"
2. Note down the group ID that appears (format: `group.XXXXXX==`)
3. Enter this group ID when prompted

### 4. Configure Environment

The script will automatically add to your `.env` file:
```
SIGNAL_PHONE_NUMBER=+16572463906
SIGNAL_GROUP_ID=group.XXXXXX==
```

### 5. Test the Setup

Run the test script to verify everything works:

```bash
python test_signal_setup.py
```

This will:
- Check Signal CLI installation
- Verify phone registration
- Send a test message to your group

## Manual Signal CLI Commands

If you need to use Signal CLI manually:

```bash
# List groups
signal-cli -u +16572463906 listGroups

# Send a message to a group
signal-cli -u +16572463906 send -g "group.XXXXXX==" -m "Test message"

# Create a new group
signal-cli -u +16572463906 updateGroup -n "Group Name" -m +16572463906

# Add members to group
signal-cli -u +16572463906 updateGroup -g "group.XXXXXX==" -m +1234567890
```

## How It Works

The system now sends reports to both Telegram and Signal:

1. **Main Scheduler** (`main.py`):
   - Generates the daily report at 8 AM PST
   - Calls `send_report_to_messengers()` which sends to both platforms

2. **Signal Messenger** (`signal_messenger.py`):
   - Handles Signal CLI integration
   - Converts Telegram markdown to plain text (Signal doesn't support markdown)
   - Sends messages via subprocess calls to signal-cli

3. **Concurrent Sending**:
   - Reports are sent to both Telegram and Signal simultaneously
   - If one fails, the other still sends
   - Both successes and failures are logged

## Troubleshooting

### Signal CLI not found
```bash
# Check if installed
ls -la ~/signal-cli/
# Reinstall
./setup_signal_cli.sh
```

### Registration fails
- Ensure the phone number can receive SMS
- Try manual registration:
  ```bash
  signal-cli -u +16572463906 register
  signal-cli -u +16572463906 verify <CODE>
  ```

### Group creation fails
- Make sure phone is registered first
- Create group manually and get ID:
  ```bash
  signal-cli -u +16572463906 updateGroup -n "Ohms Alerts Reports" -m +16572463906
  signal-cli -u +16572463906 listGroups
  ```

### Messages not sending
- Check Signal CLI works: `signal-cli --version`
- Test manual send: `signal-cli -u +16572463906 send -g "GROUP_ID" -m "Test"`
- Check logs: `tail -f /home/ohms/OhmsAlertsReports/daily-report/logs/daily_report.log`

## Service Integration

The daily report service automatically sends to both messengers. No changes needed to:
- Systemd service configuration
- Cron schedules
- Report generation

Just ensure the `.env` file has both:
- Telegram credentials (TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID)
- Signal credentials (SIGNAL_PHONE_NUMBER, SIGNAL_GROUP_ID)

## Security Notes

- Signal messages are end-to-end encrypted
- The Signal CLI stores keys in `~/.local/share/signal-cli/`
- Keep your `.env` file secure with proper permissions
- Signal groups are private by default

## Adding Group Members

To add other members to receive alerts:

1. Get their Signal phone numbers
2. Add them to the group:
   ```bash
   signal-cli -u +16572463906 updateGroup -g "GROUP_ID" -m +1234567890
   ```
3. They'll receive an invitation to join

## Monitoring

Check if messages are being sent to both platforms:

```bash
# View service logs
sudo journalctl -u daily-financial-report -f

# Check recent reports
ls -la /home/ohms/OhmsAlertsReports/daily-report/reports/
```

Both Telegram and Signal sends are logged with success/failure status.