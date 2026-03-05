---
name: marketing-promo
description: Marketing and promotional content skill — social media posts, weekly reports. Available in full and basic modes.
metadata: {"nanobot":{"emoji":"📣"}}
---

# Marketing & Promo

Available in **full mode** and **basic mode**.

## Promo Tweet Templates

Short release promo (fits 280 chars):
```
🎵 New drop: "[TITLE]" is out now!
Stream/download: [LINK]
#NewMusic #HipHop #[ARTIST]
```

Weekly highlight:
```
📊 This week: [N] streams, [N] new followers.
Latest: "[TITLE]" — check it out 👇
[LINK]
```

## Weekly Marketing Report

Gather and summarise key metrics weekly. Run every Monday at 9 AM:
```
cron(action="add", message="Generate weekly marketing report: summarise streaming numbers, social growth, and top content from the past 7 days", cron_expr="0 9 * * 1")
```

## Content Ideas (full mode)

Scan for trending topics and generate content ideas every 2 minutes (full mode only):
```
cron(action="add", message="Scan trending music/hip-hop topics and suggest 3 content ideas", cron_expr="*/2 * * * *")
```

## Platform Guidelines

### Twitter / X
- Max 280 characters per tweet
- Use 2–3 relevant hashtags
- Include a trackable link where possible

### YouTube Descriptions
- First 2 lines appear above the fold — put the key message there
- Include timestamps, links, and hashtags below

## Mode Restrictions

| Feature | full | basic |
|---------|------|-------|
| Content idea scan (every 2 min) | ✓ | ✗ |
| Weekly marketing report | ✓ | ✓ |
| Daily music promo tweet | ✓ | ✗ |
| Basic promo tweet (every 6 h) | ✗ | ✓ |
