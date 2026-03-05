---
name: basic-tweets
description: Lightweight promotional tweet composer for basic mode devices (6-12 GB RAM). No external tools required.
metadata: {"nanobot":{"emoji":"🐦"}}
---

# Basic Tweets

Available in **basic mode** (6–12 GB RAM) and **full mode**.

Compose short, punchy promotional tweets without requiring any external tools or APIs.

## Stock Promo Tweet Formats

General release:
```
🎵 "[TITLE]" available now — link in bio.
#NewMusic #[GENRE]
```

Streaming milestone:
```
🙏 [N]K streams on "[TITLE]" — thank you!
More coming soon. 👀
#[ARTIST] #HipHop
```

Behind the scenes:
```
🎚️ In the studio working on something 🔥
Stay tuned.
#NewMusic #[ARTIST]
```

Motivational / engagement:
```
What are you listening to today?
Drop your fav track 👇 #MusicMonday
```

## Cron Schedule (basic mode)

Post a promo tweet every 6 hours:
```
cron(action="add", message="Compose and post a promotional tweet using the stock templates in the basic-tweets skill", cron_expr="0 */6 * * *")
```

## Character Limit Checklist

Before posting, verify:
- [ ] ≤ 280 characters total
- [ ] Link included (or "link in bio" if over limit)
- [ ] 1–3 hashtags only
- [ ] No profanity or policy-violating content

## Mode Note

Basic mode uses `gpt-4o-mini` (cloud fallback) or `qwen2.5:0.5b-q4` (local) for text generation.
Heavy media processing (FFmpeg, video) requires upgrading to a full-mode device.
