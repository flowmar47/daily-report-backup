# WhatsApp Automation System - Complete Guide

## Overview

This WhatsApp automation system enables automated daily distribution of financial data and heatmaps to WhatsApp groups using your existing authenticated WhatsApp Web sessions.

## Architecture

### Core Components

1. **WhatsApp Automation System** (`whatsapp_automation_system.py`)
   - Core automation engine with Playwright browser control
   - Session persistence and authentication management
   - Message queuing and retry logic
   - Health monitoring and error recovery

2. **Daily Integration** (`whatsapp_daily_integration.py`)
   - Integration with existing daily report pipeline
   - Data loading from multiple sources
   - Message formatting and delivery coordination
   - Group configuration management

3. **Scheduler** (`whatsapp_scheduler.py`)
   - Automated scheduling for weekday reports
   - Integration with existing scheduling system
   - Health checks and monitoring

4. **Proof of Concept** (`whatsapp_poc_test.py`)
   - Comprehensive testing suite
   - Connection and authentication validation
   - Message and image sending tests

## Technical Specifications

### Browser Automation: Playwright (Recommended)
- ✅ **Session Persistence**: Uses existing authenticated WhatsApp Web sessions
- ✅ **Anti-Detection**: Advanced stealth measures for automation
- ✅ **Reliability**: Robust error handling and retry mechanisms
- ✅ **Performance**: Optimized for server environments (headless mode)

### Architecture Patterns
- **Async/Await**: Non-blocking operations for better performance
- **Queue Management**: Message queuing with retry logic
- **Health Monitoring**: Continuous session and connection monitoring
- **Graceful Degradation**: System continues operating despite partial failures

## Installation and Setup

### 1. Prerequisites

```bash
# Ensure Python 3.9+ is installed
python3 --version

# Install required packages
pip install playwright python-dotenv schedule asyncio

# Install Playwright browsers
playwright install chromium
```

### 2. Configuration

#### Environment Variables (.env)
Add these to your existing `.env` file:

```bash
# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER=+1234567890
WHATSAPP_GROUP_NAMES="Group 1,Group 2,Group 3"
WHATSAPP_HEADLESS=true

# Optional: Multiple groups
WHATSAPP_GROUP_1="Trading Alerts Main"
WHATSAPP_GROUP_2="Secondary Trading Group"
```

#### Configuration File (`whatsapp_automation_config.json`)
The system auto-generates this file with defaults. Key sections:

```json
{
  "browser": {
    "session_directory": "browser_sessions/whatsapp_main",
    "headless": true,
    "timeout": 30000
  },
  "groups": [
    {
      "name": "Your Group Name",
      "display_name": "Trading Group",
      "enabled": true,
      "priority": 1
    }
  ],
  "scheduling": {
    "daily_send_time": "06:00",
    "timezone": "America/Los_Angeles",
    "max_retries": 3
  }
}
```

### 3. Authentication Setup

#### Option A: Use Existing Session
If you have an authenticated WhatsApp Web session:

```bash
# Copy your existing session to the automation directory
cp -r /path/to/your/whatsapp/session browser_sessions/whatsapp_main/
```

#### Option B: New Authentication
1. Run the proof of concept in non-headless mode
2. Scan QR code when prompted
3. Session will be saved automatically

```bash
# Edit config to disable headless temporarily
# Set "headless": false in whatsapp_automation_config.json

# Run authentication test
python whatsapp_poc_test.py
```

## Usage Guide

### 1. Testing the System

#### Basic Connection Test
```bash
python whatsapp_poc_test.py
```

#### Integration Test
```bash
python whatsapp_daily_integration.py test
```

### 2. Manual Operations

#### Send Immediate Report
```bash
python whatsapp_daily_integration.py send
```

#### Send Test Report
```bash
python whatsapp_daily_integration.py send-test
```

#### Configure Groups
```bash
python whatsapp_daily_integration.py configure
```

### 3. Automated Scheduling

#### Standalone Scheduler
```bash
# Run dedicated WhatsApp scheduler
python whatsapp_scheduler.py
```

#### Integration with Existing main.py
Add WhatsApp to your existing daily report system:

```python
# Add to main.py imports
from whatsapp_daily_integration import WhatsAppDailyIntegration

# Add to DailyReportAutomation.__init__()
self.whatsapp_integration = WhatsAppDailyIntegration()

# Modify your existing report sending method
async def send_reports(self, data):
    # ... existing Signal/Telegram code ...
    
    # Add WhatsApp delivery
    try:
        # Save data for WhatsApp
        with open('live_mymama_structured_report.txt', 'w') as f:
            f.write(data)
        
        # Send via WhatsApp
        await self.whatsapp_integration.send_daily_report()
        
    except Exception as e:
        logger.error(f"WhatsApp delivery failed: {e}")
```

## Group Management

### Adding Groups
```python
from whatsapp_daily_integration import WhatsAppDailyIntegration

integration = WhatsAppDailyIntegration()
integration.add_group("New Trading Group", "Display Name", priority=1)
```

### Enabling/Disabling Groups
```python
# Disable a group temporarily
integration.enable_group("Group Name", enabled=False)

# Re-enable
integration.enable_group("Group Name", enabled=True)
```

### Group Priority Levels
- **Priority 1**: High priority - sent first
- **Priority 2**: Medium priority
- **Priority 3**: Low priority - sent last

## Content Management

### Data Sources
The system automatically loads data from:

1. **Primary**: `live_mymama_structured_report.txt`
2. **Backup**: `fresh_financial_data.txt`
3. **Output Directory**: Most recent `.txt` files

### Heatmap Sources
Automatically finds recent heatmaps from:
- `../heatmaps_package/core_files/categorical_heatmap*.png`
- `../heatmaps_package/core_files/forex_pairs*.png`

### Message Template
Customizable in config file:
```json
"message_template": "📊 Daily Financial Data Report\n\n{content}\n\n🤖 Automated via OhmsAlertsReports"
```

## Monitoring and Logging

### Log Files
- **Main**: `logs/whatsapp_automation.log`
- **Integration**: `logs/whatsapp_integration.log`
- **Scheduler**: `logs/whatsapp_scheduler.log`

### Health Checks
```python
# Manual health check
success = await whatsapp_system.health_check()
```

### Monitoring Script
```bash
# Check system status
tail -f logs/whatsapp_*.log
```

## Error Handling and Recovery

### Common Issues and Solutions

#### 1. Authentication Failures
```
⚠️ QR code detected - authentication required
```

**Solution**: 
- Run in non-headless mode
- Scan QR code
- Wait for authentication
- Switch back to headless mode

#### 2. Group Not Found
```
⚠️ Could not find Group Name group
```

**Solutions**:
- Check exact group name spelling
- Ensure group is visible in chat list
- Try searching for group first
- Update group configuration

#### 3. Session Expired
```
❌ WhatsApp authentication verification failed
```

**Solutions**:
- Delete old session: `rm -rf browser_sessions/whatsapp_main/`
- Re-authenticate with QR code
- Check session backup if available

#### 4. Message Sending Failures
```
❌ Failed to send text message
```

**Solutions**:
- Check network connectivity
- Verify group is selected
- Wait longer between messages
- Check WhatsApp Web status

### Automatic Recovery Features

1. **Session Monitoring**: Continuous authentication checks
2. **Retry Logic**: Automatic retry with exponential backoff
3. **Health Checks**: Regular system health validation
4. **Backup Sessions**: Fallback to backup session if primary fails

## Security Considerations

### Data Protection
- ✅ **No Credentials Stored**: Uses existing authenticated sessions
- ✅ **Session Encryption**: Browser sessions are encrypted
- ✅ **Log Sanitization**: Sensitive data filtered from logs
- ✅ **Test Message Prevention**: Blocks test messages to live groups

### Anti-Detection Measures
- ✅ **User Agent Rotation**: Randomized browser fingerprints
- ✅ **Human-like Delays**: Natural timing between actions
- ✅ **Stealth Scripts**: Advanced anti-detection techniques
- ✅ **Session Persistence**: Maintains long-term authentication

## Performance Optimization

### Resource Management
- **Memory Usage**: ~200MB per browser session
- **CPU Usage**: Low during idle, moderate during sending
- **Network**: Minimal bandwidth usage
- **Storage**: ~50MB for session data

### Optimization Settings
```json
{
  "browser": {
    "wait_between_messages": 2,
    "wait_between_groups": 5,
    "timeout": 30000
  },
  "reliability": {
    "health_check_interval": 300,
    "session_refresh_hours": 24
  }
}
```

## Integration with Existing System

### Hooks Integration
The system integrates with your existing Claude Code hooks:

```bash
# WhatsApp hooks validate messaging to prevent test messages
./.claude-hooks/messaging-validation.sh
```

### Makefile Integration
Add to your existing Makefile:

```makefile
whatsapp-test: ## Test WhatsApp automation
	python whatsapp_poc_test.py

whatsapp-send: ## Send immediate WhatsApp report
	python whatsapp_daily_integration.py send

whatsapp-configure: ## Configure WhatsApp groups
	python whatsapp_daily_integration.py configure
```

## Production Deployment

### Systemd Service
Create `/etc/systemd/system/whatsapp-automation.service`:

```ini
[Unit]
Description=WhatsApp Financial Automation
After=network.target

[Service]
Type=simple
User=ohms
WorkingDirectory=/home/ohms/OhmsAlertsReports/daily-report
Environment=DISPLAY=:1
ExecStart=/home/ohms/OhmsAlertsReports/daily-report/venv/bin/python whatsapp_scheduler.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### Service Management
```bash
# Enable and start service
sudo systemctl enable whatsapp-automation.service
sudo systemctl start whatsapp-automation.service

# Monitor service
sudo systemctl status whatsapp-automation.service
sudo journalctl -u whatsapp-automation.service -f
```

### Backup and Recovery
```bash
# Backup WhatsApp sessions
tar -czf whatsapp_sessions_backup.tar.gz browser_sessions/

# Restore sessions
tar -xzf whatsapp_sessions_backup.tar.gz
```

## Troubleshooting

### Debug Mode
Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing
```bash
# Test individual components
python -c "
import asyncio
from whatsapp_automation_system import WhatsAppAutomationSystem

async def test():
    system = WhatsAppAutomationSystem()
    await system.initialize()
    await system.find_group('Your Group Name')
    await system.cleanup()

asyncio.run(test())
"
```

### Common Command Reference
```bash
# Full system test
python whatsapp_poc_test.py

# Quick integration test
python whatsapp_daily_integration.py test

# Send test message
python whatsapp_daily_integration.py send-test

# Configure groups
python whatsapp_daily_integration.py configure

# Check logs
tail -f logs/whatsapp_*.log

# Restart authentication
rm -rf browser_sessions/whatsapp_main/ && python whatsapp_poc_test.py
```

## Support and Maintenance

### Regular Maintenance
1. **Weekly**: Check log files for errors
2. **Monthly**: Update browser dependencies
3. **Quarterly**: Refresh authentication sessions
4. **As Needed**: Update group configurations

### Updates and Upgrades
```bash
# Update Playwright
pip install --upgrade playwright
playwright install chromium

# Update dependencies
pip install --upgrade -r requirements.txt
```

### Getting Help
1. Check logs for specific error messages
2. Run diagnostic tests with `whatsapp_poc_test.py`
3. Verify configuration with `whatsapp_daily_integration.py test`
4. Review authentication status in WhatsApp Web

## Best Practices

### 1. Group Management
- Use descriptive group names
- Test with a single group first
- Enable groups gradually
- Monitor delivery success rates

### 2. Content Quality
- Keep messages concise and professional
- Include timestamp information
- Test message formatting before automation
- Ensure heatmap images are optimized

### 3. Reliability
- Run health checks regularly
- Monitor authentication status
- Keep backup sessions
- Test recovery procedures

### 4. Security
- Never commit session data to version control
- Use environment variables for sensitive config
- Monitor for unauthorized access
- Regularly rotate authentication sessions

## Conclusion

This WhatsApp automation system provides reliable, secure, and efficient delivery of daily financial reports to your trading groups. The system is designed to integrate seamlessly with your existing infrastructure while maintaining the highest standards of security and reliability.

For additional support or questions, refer to the troubleshooting section or check the system logs for specific error details.