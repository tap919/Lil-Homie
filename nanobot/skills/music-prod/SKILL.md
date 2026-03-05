---
name: music-prod
description: Music production skill — audio processing, beat backup, and project management. Requires full mode (12 GB+ RAM).
metadata: {"nanobot":{"emoji":"🎶","requires":{"bins":["ffmpeg"]}}}
---

# Music Production

**Requires full mode** (12 GB+ RAM, 8-core CPU, NPU, Android 14+).

Use FFmpeg for audio processing and the git tool for beat project backups.

## Audio Processing with FFmpeg

Convert audio format:
```bash
ffmpeg -i input.wav -codec:a libmp3lame -qscale:a 2 output.mp3
```

Normalize loudness (LUFS target for streaming):
```bash
ffmpeg -i input.wav -af loudnorm=I=-14:LRA=11:TP=-1 output_normalized.wav
```

Trim a clip:
```bash
ffmpeg -i beat.wav -ss 00:00:10 -to 00:01:30 -c copy clip.wav
```

Create a simple video montage (image + audio):
```bash
ffmpeg -loop 1 -i cover.jpg -i beat.mp3 -c:v libx264 -tune stillimage \
       -c:a aac -b:a 192k -pix_fmt yuv420p -shortest promo.mp4
```

## Beat Backup

Back up the beats directory to a timestamped archive:
```bash
BACKUP_DIR="/storage/emulated/0/Android/data/lil-homie/backups"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/beats-$(date +%Y%m%d).tar.gz" ~/beats/
```

Or use git for versioned project management:
```bash
cd ~/beats-project
git add -A
git commit -m "nightly backup $(date +%Y-%m-%d)"
```

## Cron Schedule (full mode only)

| Job | Schedule | Command |
|-----|----------|---------|
| daily-music-promo | `0 10 * * *` | tweet latest release |
| nightly-music-backup | `0 2 * * *` | backup beats to storage |

To add the backup job via Lil Homie cron:
```
cron(action="add", message="Run nightly beats backup", cron_expr="0 2 * * *")
```
