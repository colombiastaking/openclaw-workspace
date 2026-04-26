# Colombia Staking Announcements

## Overview

This skill handles posting announcements to Colombia Staking Telegram groups.

## Telegram Groups

| Group | Language | ID | Notes |
|-------|----------|-----|-------|
| ColombiaStakingAnn | English | `-1001656543676` | Main announcement channel |
| colombiastakingesp | Spanish | `-1003060491428` | Spanish group |
| colmbiastakingfr | French | `-1002660077574` | French group |
| ColombiaStakingChat | English | `-1001567513982` | **DO NOT POST** - they get updates from announcement channel |

## Workflow

When Sebas asks to post an announcement:

### Step 1: Post to Announcement Channel
- Language: **English** (original)
- Channel: `ColombiaStakingAnn` (`-1001656543676`)

### Step 2: Post to Language Groups
- **Spanish**: `colombiastakingesp` (`-1003060491428`)
- **French**: `colmbiastakingfr` (`-1002660077574`)

### Step 3: Skip English Main Group
- **DO NOT** post to `ColombiaStakingChat` (`-1001567513982`)
- They will receive updates by following the announcement channel

## Translation Guidelines

- Translate the announcement to Spanish and French
- Keep the same formatting and links
- Use clean posts without translation notes
- Include all media (images, links, etc.)

## Example

**Input from Sebas:**
```
Hey, check this out: @ColombiaStaking Dapp is all fresh and updated to SDK5! Also, take a peek at our brand new website: staking.colombia-staking.com
```

**Actions:**
1. Post English to `-1001656543676` (ColombiaStakingAnn)
2. Post Spanish to `-1003060491428` (colombiastakingesp)
3. Post French to `-1002660077574` (colmbiastakingfr)
4. **DO NOT** post to `-1001567513982` (ColombiaStakingChat)

## Commands

The announcement should be sent via the `message` tool:

```javascript
// Announcement channel (English)
message({
  action: "send",
  channel: "telegram",
  message: "...",
  target: "-1001656543676"
});

// Spanish group
message({
  action: "send",
  channel: "telegram",
  message: "Translated Spanish message...",
  target: "-1003060491428"
});

// French group
message({
  action: "send",
  channel: "telegram",
  message: "Translated French message...",
  target: "-1002660077574"
});
```

## Notes

- This workflow applies to all official Colombia Staking announcements
- Always translate to ES/FR, not just copy the English
- Include all original links and formatting
- Never post English to ColombiaStakingChat - they follow the announcement channel
