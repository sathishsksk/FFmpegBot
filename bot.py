#!/usr/bin/env python3
import asyncio
import logging
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ChatAction, ParseMode
from pyrogram.types import Message

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
APP_ID    = int(os.getenv("APP_ID", 0))
APP_HASH  = os.getenv("APP_HASH", "")
OWNER_ID  = int(os.getenv("OWNER_ID", 0))
PORT      = int(os.getenv("PORT", 8000))
TMPDIR    = "/app/tmp"
os.makedirs(TMPDIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Presets ───────────────────────────────────────────────────────────────────
PRESETS = {
    "hevc10": {
        "desc": "HEVC H.265 10-bit 1080p (best quality)",
        "cmd": "-i {input} -vf scale=-2:1080 -c:v libx265 -crf 28 -preset medium -profile:v main10 -pix_fmt yuv420p10le -c:a copy {output}.mkv",
        "ext": ".mkv",
    },
    "hevc": {
        "desc": "HEVC H.265 8-bit 1080p",
        "cmd": "-i {input} -vf scale=-2:1080 -c:v libx265 -crf 28 -preset medium -c:a copy {output}.mkv",
        "ext": ".mkv",
    },
    "h264": {
        "desc": "H.264 1080p (widely compatible)",
        "cmd": "-i {input} -vf scale=-2:1080 -c:v libx264 -crf 23 -preset medium -c:a copy {output}.mp4",
        "ext": ".mp4",
    },
    "compress": {
        "desc": "Compress to 720p smaller file",
        "cmd": "-i {input} -c:v libx264 -crf 32 -preset slow -vf scale=-2:720 -c:a aac -b:a 128k {output}.mp4",
        "ext": ".mp4",
    },
    "mp3": {
        "desc": "Extract audio → MP3 320kbps",
        "cmd": "-i {input} -vn -c:a libmp3lame -q:a 0 {output}.mp3",
        "ext": ".mp3",
    },
    "m4a": {
        "desc": "Extract audio → M4A best quality",
        "cmd": "-i {input} -vn -c:a aac -b:a 320k {output}.m4a",
        "ext": ".m4a",
    },
    "720p": {
        "desc": "Resize to 720p H.264",
        "cmd": "-i {input} -vf scale=-2:720 -c:v libx264 -crf 23 -preset medium -c:a copy {output}.mp4",
        "ext": ".mp4",
    },
    "480p": {
        "desc": "Resize to 480p H.264",
        "cmd": "-i {input} -vf scale=-2:480 -c:v libx264 -crf 23 -preset medium -c:a copy {output}.mp4",
        "ext": ".mp4",
    },
    "trim": {
        "desc": "Trim first 60 seconds",
        "cmd": "-i {input} -ss 00:00:00 -t 00:01:00 -c copy {output}.mkv",
        "ext": ".mkv",
    },
}

# ── Health check ──────────────────────────────────────────────────────────────
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass

def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"[Health] Running on port {PORT} → GET /health")

# ── Bot ───────────────────────────────────────────────────────────────────────
app = Client("ffmpeg_bot", api_id=APP_ID, api_hash=APP_HASH, bot_token=BOT_TOKEN)

def build_presets_text():
    lines = ["**Available presets:**\n"]
    for key, val in PRESETS.items():
        lines.append(f"• `{key}` — {val['desc']}")
    return "\n".join(lines)

async def run_ffmpeg(cmd):
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    return proc.returncode == 0, stderr.decode(errors="replace")

@app.on_message(filters.command("start"))
async def cmd_start(client, message: Message):
    await message.reply_text(
        "👋 **FFmpeg Bot**\n\n"
        "Send me any video, audio, or document file and I'll convert it.\n\n"
        "**How to use:**\n"
        "1️⃣ Send a file\n"
        "2️⃣ Reply to it with:\n"
        "   `/convert hevc10`\n"
        "   `/convert mp3`\n\n"
        "Or custom FFmpeg args:\n"
        "   `/custom -c:v libx264 -crf 23 -c:a copy`\n\n"
        "Type /presets to see all presets.",
        parse_mode=ParseMode.MARKDOWN,
    )

@app.on_message(filters.command("presets"))
async def cmd_presets(client, message: Message):
    await message.reply_text(build_presets_text(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("help"))
async def cmd_help(client, message: Message):
    await message.reply_text(
        "**Commands:**\n"
        "`/presets` — List all presets\n"
        "`/convert <preset>` — Reply to a file to convert\n"
        "`/custom <args>` — Reply to a file with custom FFmpeg args\n\n"
        "**Example:**\n"
        "Send video → reply `/convert hevc10`",
        parse_mode=ParseMode.MARKDOWN,
    )

@app.on_message(filters.command("convert"))
async def cmd_convert(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to a file with `/convert <preset>`", parse_mode=ParseMode.MARKDOWN)
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("⚠️ Specify a preset. Example: `/convert hevc10`", parse_mode=ParseMode.MARKDOWN)
        return
    preset_key = args[1].strip().lower()
    if preset_key not in PRESETS:
        await message.reply_text(f"❌ Unknown preset `{preset_key}`\n\nType /presets for list.", parse_mode=ParseMode.MARKDOWN)
        return
    await process_file(client, message, message.reply_to_message, preset_key=preset_key)

@app.on_message(filters.command("custom"))
async def cmd_custom(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to a file with `/custom <ffmpeg args>`", parse_mode=ParseMode.MARKDOWN)
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("⚠️ Provide FFmpeg arguments.\nExample: `/custom -c:v libx264 -crf 23 -c:a copy`", parse_mode=ParseMode.MARKDOWN)
        return
    await process_file(client, message, message.reply_to_message, custom_args=args[1].strip())

async def process_file(client, message, file_message, preset_key=None, custom_args=None):
    media = (
        file_message.video or file_message.document or
        file_message.audio or file_message.voice or file_message.video_note
    )
    if not media:
        await message.reply_text("❌ No supported file found. Send a video, audio, or document.")
        return

    status_msg = await message.reply_text("⬇️ Downloading file...")
    await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)

    with tempfile.TemporaryDirectory(dir=TMPDIR) as tmpdir:
        try:
            input_path = await client.download_media(file_message, file_name=os.path.join(tmpdir, "input"))
        except Exception as e:
            await status_msg.edit_text(f"❌ Download failed: {e}")
            return

        input_path = Path(input_path)
        stem = input_path.stem

        if preset_key:
            preset = PRESETS[preset_key]
            output_path = Path(tmpdir) / f"{stem}_converted{preset['ext']}"
            ffmpeg_args = (
                preset["cmd"]
                .replace("{input}", str(input_path))
                .replace("{output}", str(output_path.with_suffix("")))
                .split()
            )
        else:
            output_path = Path(tmpdir) / f"{stem}_converted.mkv"
            ffmpeg_args = ["-i", str(input_path)] + custom_args.split() + [str(output_path)]

        await status_msg.edit_text("⚙️ Converting... Please wait.")
        success, stderr = await run_ffmpeg(ffmpeg_args)

        if not success or not output_path.exists():
            error_lines = "\n".join(stderr.strip().splitlines()[-10:])
            await status_msg.edit_text(f"❌ FFmpeg failed:\n```\n{error_lines}\n```", parse_mode=ParseMode.MARKDOWN)
            return

        await status_msg.edit_text("⬆️ Uploading result...")
        size_mb = output_path.stat().st_size / (1024 * 1024)
        caption = (
            f"✅ **Done!**\nPreset: `{preset_key}`\nSize: `{size_mb:.1f} MB`"
            if preset_key else
            f"✅ **Done!**\nSize: `{size_mb:.1f} MB`"
        )
        try:
            await client.send_document(
                message.chat.id,
                document=str(output_path),
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.id,
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ Upload failed: {e}")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    start_health_server()
    logger.info("Starting FFmpeg Bot...")
    app.run()
