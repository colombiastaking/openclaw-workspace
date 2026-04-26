# Agent-Browser Installation (March 8, 2026)

## What is it
Vercel's `agent-browser` CLI - headless browser automation that works on Pi without GUI.

## Installed on Pi
- npm package: `agent-browser`
- Chromium downloaded: `chromium-headless-shell` v1208

## How to use
```bash
agent-browser open <url>     # Open a page
agent-browser snapshot        # Get accessibility tree
agent-browser click <ref>   # Click element
agent-browser fill <ref> "text"  # Fill form
agent-browser screenshot    # Take screenshot
agent-browser close        # Close browser
```

## Working Sites
- Google ✅
- Binance ✅
- Colombia Staking DApp ✅
- Most websites ✅

## Not Working
- Polymarket (connection reset/geo-blocked)

## Auto-Update Note
Check for agent-browser updates periodically:
```bash
npm install -g agent-browser
agent-browser install  # Update Chromium
```

Update this note when reinstalling/updating!
