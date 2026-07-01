# FFmpeg Telegram Bot

A Telegram bot that converts videos, audio, and files using FFmpeg — deployable on Koyeb with one click.

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/YOUR_USERNAME/ffmpeg-bot&branch=main&name=ffmpeg-bot)

> Replace `YOUR_USERNAME` in the button URL with your GitHub username after pushing.

## One-Click Deploy

Click the button above. Koyeb will ask for these values:

| Variable | Required | What to put |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `APP_ID` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `APP_HASH` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `OWNER_ID` | ✅ | Your Telegram user ID from [@userinfobot](https://t.me/userinfobot) |
| `PORT` | Pre-filled | Leave as `8000` |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick guide |
| `/presets` | List all available conversion presets |
| `/help` | Full usage instructions |
| `/convert <preset>` | Reply to a file to convert using a preset |
| `/custom <args>` | Reply to a file with custom FFmpeg arguments |

## Available Presets

| Preset | Output | Description |
|--------|--------|-------------|
| `hevc10` | MKV | HEVC H.265 10-bit 1080p — best quality |
| `hevc` | MKV | HEVC H.265 8-bit 1080p |
| `h264` | MP4 | H.264 1080p — widely compatible |
| `compress` | MP4 | Compress to 720p smaller file |
| `mp3` | MP3 | Extract audio, 320kbps |
| `m4a` | M4A | Extract audio, AAC best quality |
| `720p` | MP4 | Resize to 720p H.264 |
| `480p` | MP4 | Resize to 480p H.264 |
| `trim` | MKV | Trim first 60 seconds |

## Usage Examples

**Convert AV1 video to HEVC 10-bit:**
1. Send the video file to the bot
2. Reply to it with `/convert hevc10`
3. Bot downloads, converts, and sends back the result

**Custom FFmpeg command:**
1. Send the video file
2. Reply with `/custom -c:v libx264 -crf 18 -c:a copy`
3. Bot wraps it as `ffmpeg -i input <your args> output`

## Adding Custom Presets

Edit `src/presets.py` and add a new entry:

```python
"mypreset": {
    "desc": "My custom conversion",
    "cmd": "-i {input} -c:v libx264 -crf 23 -c:a copy {output}.mp4",
    "ext": ".mp4",
},
```

Then push and redeploy — no other changes needed.

## Health Check

```
GET /health → 200 OK {"status": "ok"}
```

Automatically wired into `koyeb.yaml`.
