# Archived Documentation

This directory contains documentation files that are no longer relevant to the current API-based signal generation system.

## Why These Were Archived

The system has transitioned from:
- **Web scraping (MyMama.uk)** to **Live API data retrieval** from multiple financial data sources
- **WhatsApp messaging** was removed in favor of Signal + Telegram only
- **Heatmap generation** has been separated into an independent system

## Archived Files

### WhatsApp Integration (Deprecated)
- `WHATSAPP_INTEGRATION_STATUS.md` - WhatsApp integration status
- `WHATSAPP_INTEGRATION_FINAL.md` - Final WhatsApp setup guide
- `WHATSAPP_AUTOMATION_GUIDE.md` - WhatsApp automation documentation
- `WHATSAPP_INTEGRATION_SUMMARY.md` - WhatsApp implementation summary

WhatsApp messaging was removed from the daily signal system due to reliability issues and API limitations.

### Heatmap Integration (Separated)
- `HEATMAP_INTEGRATION_COMPLETE.md` - Heatmap completion documentation
- `HEATMAP_INTEGRATION_SUMMARY.md` - Heatmap implementation summary

Heatmap generation has been moved to a separate independent system and is no longer part of the daily forex signal pipeline.

## Current System

The current system uses:
- **API-based data retrieval** from 8+ financial data sources
- **Multi-factor signal analysis** (Technical 75%, Economic 20%, Geopolitical 5%)
- **Signal + Telegram** messaging for signal delivery
- **Cron-based scheduling** for 6 AM PST weekday execution

See the main `README.md` and `CLAUDE.md` for current system documentation.

---
*Archived: January 2026*
