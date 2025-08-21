# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Codebase Overview

This is a financial alerts automation system that scrapes trading signals from MyMama.uk and distributes them via Signal and Telegram messengers. The system runs on scheduled basis (8 AM PST weekdays) to deliver structured financial reports using a specific plaintext format.

## Architecture

### Core Components

**Main Application**: `main.py` - Central orchestrator using asyncio for concurrent operations
- Coordinates scraping, processing, and messaging
- Manages browser sessions and security utilities  
- Handles scheduled execution with retry logic
- Uses Python `schedule` library for weekday automation

**Scrapers**: Browser-based scraper implementation focusing on MyMama.uk
- `real_only_mymama_scraper.py` - Primary scraper (real alerts only, no synthetic fallbacks)
- Uses Playwright for browser automation with anti-detection measures
- Session persistence in `browser_sessions/` for authentication reuse
- Handles dynamic content loading and authentication modals

**Data Processing**: Structured data models with exact plaintext format compliance
- `src/data_processors/template_generator.py` - `StructuredTemplateGenerator` class generates exact output format
- `src/data_processors/data_models.py` - Data classes for forex, options, earnings, swing/day trades
- `src/data_processors/financial_alerts.py` - Processes raw scraped content into structured formats
- Output follows exact plaintext specification (NO emojis, specific headers)

**Messaging**: Dual-platform notification system
- `messengers/signal_messenger.py` - Signal integration via signal-cli Docker API
- `messengers/telegram_messenger.py` - Telegram Bot API integration  
- `messengers/multi_messenger.py` - Unified interface for concurrent delivery
- Both use `send_structured_financial_data()` method for consistent formatting

**Configuration**: Environment-based configuration management
- `config.json` - Main scheduling, scraping, and security settings
- `.env` file for sensitive credentials (NEVER commit)
- `src/config/settings.py` - Settings loader with environment variable support

### Critical Design Patterns

**Scheduled Execution**: Runs Monday-Friday at 08:00 America/Los_Angeles timezone
**AUTHENTIC DATA ONLY**: NEVER use simulated, synthetic, fake, or fallback data - ONLY real MyMama alerts
**Plaintext Format**: Specific text format without emojis, exact header requirements
**Dual Messaging**: Concurrent delivery to both Signal and Telegram with error handling
**Session Management**: Browser session persistence across runs for authentication
**Anti-Detection**: User agent rotation, human-like delays, fingerprint protection

## Common Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies  
pip install -r requirements.txt

# Setup environment variables (required)
cp .env.template .env
# Edit .env with actual credentials before running
```

### Core Testing Commands
```bash
# Test complete system end-to-end
python test_complete_fixed_system.py

# Test plaintext format output
python verify_plaintext_fix.py

# Test structured template generation
python test_complete_structured_pipeline.py

# Test individual components
python test_mymama_messengers.py          # Message delivery
python test_forex_extraction.py           # Data extraction  
python test_essentials_page.py            # Page scraping
python real_only_mymama_scraper.py        # Primary scraper
```

### Running the System
```bash
# Run main application (scheduled mode - production)
source venv/bin/activate && python main.py

# Send immediate test report
python send_immediate_report.py

# Send to both messengers manually
python send_to_both_messengers.py

# Check system health
python system_health_check.py
```

### Signal Integration Setup
```bash
# Initial Signal registration (one-time setup)
python register_signal.py

# Verify Signal connectivity
python check_signal_status.py

# Complete Signal group verification
python complete_signal_verification.py

# Update Signal group configuration
python update_signal_config.py
```

### Debugging and Maintenance
```bash
# Check process status
ps aux | grep main.py

# View live logs
tail -f logs/daily_report.log

# Test format without sending
python test_old_format.py

# Restart main process (after code changes)
pkill -f main.py && source venv/bin/activate && nohup python main.py > logs/main_restart.log 2>&1 &
```

## Configuration Requirements

### Environment Variables (.env)
```
MYMAMA_USERNAME=your_username
MYMAMA_PASSWORD=your_password
MYMAMA_GUEST_PASSWORD=guest_password_if_needed

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_GROUP_ID=your_group_id

SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_GROUP_ID=your_signal_group_id
```

### Key Configuration Areas
- **Scheduling**: `config.json` → `app_settings.report_time` (default: 08:00 PST)
- **Scraping**: Anti-detection settings, timeouts, session persistence
- **Security**: Rate limiting, proxy rotation, data anonymization
- **Messaging**: Platform-specific formatting and delivery settings

## Data Flow Architecture

1. **Scheduled Trigger** → `main.py` starts at 08:00 weekdays via Python `schedule`
2. **Browser Setup** → Playwright with session persistence and anti-detection
3. **Authentication** → MyMama.uk login using stored credentials, handles modals
4. **Content Loading** → Dynamic scrolling to load all content sections
5. **Data Extraction** → `real_only_mymama_scraper.py` extracts raw HTML/text
6. **Data Processing** → `FinancialAlertsProcessor` converts to structured data models
7. **Template Generation** → `StructuredTemplateGenerator` creates exact plaintext format
8. **Dual Delivery** → Concurrent messaging via `send_structured_financial_data()`
9. **Session Persistence** → Browser state saved for next authentication

### Message Flow Priority
1. **Primary**: `send_structured_financial_data()` using `StructuredTemplateGenerator`
2. **Fallback**: `generate_report()` also uses structured template (NOT legacy emoji format)
3. **Both paths**: Must produce identical plaintext format output

### Critical Success Factors
- MyMama.uk authentication must succeed
- Real data extraction (forex, options, earnings) required - NO SYNTHETIC DATA ALLOWED
- Both Signal and Telegram delivery must complete
- Output format must match exact plaintext specification

### CRITICAL: Data Authenticity Requirements
**NEVER GENERATE OR USE:**
- Simulated trading data
- Synthetic financial alerts  
- Fake forex pairs or prices
- Mock earnings data
- Placeholder trading signals
- Sample or test financial content

**ALWAYS VERIFY:**
- Data comes directly from MyMama.uk scraping
- No fallback or default values are used
- System fails gracefully if no real data available
- Reports are only sent when authentic data exists

## Important Notes

### Scraping Strategy
- **Primary URL**: `https://www.mymama.uk/copy-of-alerts-essentials-1`
- **AUTHENTIC DATA ONLY**: Zero tolerance for synthetic, simulated, or fallback data
- **Content Sections**: Forex (top), Earnings (middle), Options (bottom)
- **Authentication**: Handles login modals with specific CSS selectors
- **No Data = No Report**: System must NOT send anything if real data unavailable

### CRITICAL: Output Format Requirements
The system MUST produce structured output in exact plaintext format (NO emojis):

**Forex Section:**
```
FOREX PAIRS

Pair: EURUSD
High: 1.1158
Average: 1.0742
Low: 1.0238
MT4 Action: MT4 SELL
Exit: 1.0850
```

**Options Section:**
```
EQUITIES AND OPTIONS

Symbol: QQQ
52 Week High: 480.92
52 Week Low: 478.13
Strike Price:

CALL > 521.68

PUT < N/A
Status: TRADE IN PROFIT
```

**Premium Trades:**
```
PREMIUM SWING TRADES (Monday - Wednesday)

JOYY Inc. (JOYY)
Earnings Report: May 26, 2025
Current Price: $47.67
Rationale: [detailed rationale text]
```

**Key Format Rules:**
- NO emojis anywhere in output (🔴, 📊, etc.)
- Use "MT4 Action:" NOT "Trade Type:"
- Use "Symbol:" NOT "Ticker:" for options
- Exact section headers as shown above
- Reference `sample_structured_output.txt` for format template

### Security Considerations
- Credentials stored in `.env` (never commit)
- Session files in `browser_sessions/` (gitignored)
- Rate limiting and request throttling
- User-Agent rotation and anti-detection measures
- Data sanitization before storage

### Testing Strategy
- Component-level tests for scrapers, processors, messengers
- Integration tests for complete workflows
- Signal/Telegram connectivity tests
- Authentication and session persistence tests

## Development Workflow

### Making Changes to Output Format
1. **Always test format first**: Use `verify_plaintext_fix.py` or `test_old_format.py`
2. **Key files to modify**:
   - `src/data_processors/data_models.py` - Data class `format_output()` methods
   - `src/data_processors/template_generator.py` - `StructuredTemplateGenerator`
3. **Never modify**: Legacy emoji format methods (they're removed)
4. **Test pipeline**: Use `test_complete_structured_pipeline.py`

### Deployment Process
1. **Test locally**: Verify format and messaging with test scripts
2. **Update main process**: `pkill -f main.py && source venv/bin/activate && nohup python main.py > logs/main_restart.log 2>&1 &`
3. **Verify scheduling**: Check `ps aux | grep main.py` and logs
4. **Monitor logs**: `tail -f logs/daily_report.log` for next scheduled run

### Troubleshooting Common Issues
- **Wrong format sent**: Check if `_generate_legacy_report()` or `generate_report()` are using emojis
- **Authentication failures**: Check MyMama.uk credentials in `.env` and session persistence
- **Signal/Telegram failures**: Verify credentials and test individual messengers
- **Scheduling issues**: Ensure virtual environment is activated when starting main.py

### Critical Success Metrics
- Exact plaintext format compliance (NO emojis)
- Successful authentication to MyMama.uk  
- Real data extraction (ZERO synthetic, simulated, or fake data tolerance)
- Concurrent delivery to both messaging platforms
- Reliable weekday scheduling at 08:00 PST

## ABSOLUTE PROHIBITIONS

### Data Authenticity Rules
**NEVER, UNDER ANY CIRCUMSTANCES:**
1. **Generate synthetic financial data** (forex rates, stock prices, earnings)
2. **Create simulated trading alerts** or mock signals
3. **Use placeholder or sample data** in production messages
4. **Implement fallback data generation** when scraping fails
5. **Send reports with fake, estimated, or interpolated values**
6. **Create test data that could be mistaken for real alerts**

**ALWAYS FAIL GRACEFULLY:**
- If MyMama.uk is unavailable → NO report sent
- If authentication fails → NO report sent  
- If scraping returns empty → NO report sent
- If data appears corrupted → NO report sent

**WHY THIS MATTERS:**
This system provides financial trading signals to real users. Synthetic or fake data could result in:
- Financial losses from bad trading decisions
- Legal liability for providing false information
- Loss of trust and credibility
- Regulatory violations

**When in doubt: NO DATA = NO REPORT**