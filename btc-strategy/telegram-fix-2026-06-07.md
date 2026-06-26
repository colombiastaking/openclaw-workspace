# BTC Strategy Telegram Fix - 2026-06-07

## Problem
Morning BTC report (score: 15) failed to send via Telegram with error:
```
404 - {"ok":false,"error_code":404,"description":"Not Found"}
```

## Root Cause
The `daily_strategy_report_v3.py` script had a **fallback token with ellipsis** (`…`):
```python
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "[REDACTED]")
```

When the cron job's `source` command didn't work properly, the script fell back to this invalid truncated token, causing 404 errors.

## Fix Applied
1. **Updated fallback token** in script to full correct token:
   ```python
   TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "[REDACTED — stored in local env only]")
   ```

2. **Added comment warning** never to truncate the token.

3. **Verified cron job** properly sources env file before running script.

## Verification
- Test message sent successfully ✅
- Report resent successfully ✅  
- Script now has reliable fallback ✅

## Files Modified
- `/home/raspberry/.openclaw/workspace/.agents/skills/btc-strategy/scripts/daily_strategy_report_v3.py` (line 22)

## Prevention
- Never use truncated tokens in code
- Always verify env var loading in cron jobs
- Test Telegram delivery after any script changes
