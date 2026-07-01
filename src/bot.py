#!/usr/bin/env python3
import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.enums import ChatAction, ParseMode
from pyrogram.types import Message

from config import APP_ID, APP_HASH, BOT_TOKEN, OWNER_ID
from health import start_health_server
from presets import PRESETS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Client("ffmpeg_bot", api_id=APP_ID, api_hash=APP_HASH, bot_token=BOT_TOKEN)

TMPDIR = "/app/tmp"
os.makedirs(TMPDIR, exist_ok=True)

# ─── Helpers ────────────────────────────────────────────────────────────────

def build_presets_text():
    lines = ["**Available presets:**\n"]
    for key, val in PRESETS.items():
        lines.append(f"• `{key}` — {val['desc']}")
    return "\n".join(lines)

async def run_ffmpeg(cmd: list[str]) -> tuple[bool, str]:
    """Run an ffmpeg command, return (success, stderr)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        return proc.returncode == 0, stderr.decode(errors="replace")
    except Exception as e:
        return False, str(e)

# ─── Commands ────────────────────────────────────────────────────────────────

@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    await message.reply_text(
        "👋 **FFmpeg Bot**\n\n"
        "Send me any video, audio, or document file and I'll convert it.\n\n"
        "**How to use:**\n"
        "1️⃣ Send a file\n"
        "2️⃣ Reply to it with a preset name:\n"
        "   `/convert hevc10`\n"
        "   `/convert mp3`\n\n"
        "Or use a custom FFmpeg command:\n"
        "   `/custom -c:v libx264 -crf 23 -c:a copy`\n\n"
        "Type /presets to see all available presets.",
        parse_mode=ParseMode.MARKDOWN,
    )

@app.on_message(filters.command("presets"))
async def cmd_presets(client: Client, message: Message):
    await message.reply_text(build_presets_text(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("help"))
async def cmd_help(client: Client, message: Message):
    await message.reply_text(
        "**FFmpeg Bot — Help**\n\n"
        "`/presets` — List all conversion presets\n"
        "`/convert <preset>` — Reply to a file to convert it\n"
        "`/custom <args>` — Reply to a file with custom FFmpeg args\n\n"
        "**Example — preset:**\n"
        "Send a video → reply with `/convert hevc10`\n\n"
        "**Example — custom:**\n"
        "Send a video → reply with:\n"
        "`/custom -c:v libx264 -crf 23 -c:a copy`\n\n"
        "The bot automatically adds `-i input` and `output` — "
        "just write the middle arguments.",
        parse_mode=ParseMode.MARKDOWN,
    )

# ─── /convert <preset> ───────────────────────────────────────────────────────

@app.on_message(filters.command("convert"))
async def cmd_convert(client: Client, message: Message):
    # Must be a reply to a file
    if not message.reply_to_message:
        await message.reply_text(
            "⚠️ Reply to a file with `/convert <preset>`\n\nType /presets for list.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text(
            "⚠️ Specify a preset. Example: `/convert hevc10`\n\nType /presets for list.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    preset_key = args[1].strip().lower()
    if preset_key not in PRESETS:
        await message.reply_text(
            f"❌ Unknown preset `{preset_key}`\n\nType /presets for list.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await process_file(client, message, message.reply_to_message, preset_key=preset_key)

# ─── /custom <args> ──────────────────────────────────────────────────────────

@app.on_message(filters.command("custom"))
async def cmd_custom(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text(
            "⚠️ Reply to a file with `/custom <ffmpeg args>`\n\n"
            "Example: `/custom -c:v libx264 -crf 23 -c:a copy`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text(
            "⚠️ Provide FFmpeg arguments.\n"
            "Example: `/custom -c:v libx264 -crf 23 -c:a copy`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    custom_args = args[1].strip()
    await process_file(client, message, message.reply_to_message, custom_args=custom_args)

# ─── Core processor ──────────────────────────────────────────────────────────

async def process_file(
    client: Client,
    message: Message,
    file_message: Message,
    preset_key: str = None,
    custom_args: str = None,
):
    # Determine file from the replied-to message
    media = (
        file_message.video
        or file_message.document
        or file_message.audio
        or file_message.voice
        or file_message.video_note
    )
    if not media:
        await message.reply_text("❌ No supported file found. Send a video, audio, or document.")
        return

    status_msg = await message.reply_text("⬇️ Downloading file...")
    await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)

    with tempfile.TemporaryDirectory(dir=TMPDIR) as tmpdir:
        # Download
        try:
            input_path = await client.download_media(file_message, file_name=os.path.join(tmpdir, "input"))
        except Exception as e:
            await status_msg.edit_text(f"❌ Download failed: {e}")
            return

        input_path = Path(input_path)
        stem = input_path.stem

        # Build ffmpeg command
        if preset_key:
            preset = PRESETS[preset_key]
            output_ext = preset["ext"]
            output_path = Path(tmpdir) / f"{stem}_converted{output_ext}"
            ffmpeg_args = (
                preset["cmd"]
                .replace("{input}", str(input_path))
                .replace("{output}", str(output_path.with_suffix("")))
                .split()
            )
        else:
            # Custom args — user provides middle args, we wrap with -i and output
            output_path = Path(tmpdir) / f"{stem}_converted.mkv"
            ffmpeg_args = ["-i", str(input_path)] + custom_args.split() + [str(output_path)]

        # Run ffmpeg
        await status_msg.edit_text("⚙️ Converting... Please wait.")
        success, stderr = await run_ffmpeg(ffmpeg_args)

        if not success or not output_path.exists():
            # Show last 10 lines of ffmpeg error
            error_lines = "\n".join(stderr.strip().splitlines()[-10:])
            await status_msg.edit_text(
                f"❌ FFmpeg failed:\n```\n{error_lines}\n```",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Upload result
        await status_msg.edit_text("⬆️ Uploading result...")
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        caption = (
            f"✅ **Done!**\n"
            f"Preset: `{preset_key}`\n"
            f"Size: `{file_size_mb:.1f} MB`"
            if preset_key else
            f"✅ **Done!**\n"
            f"Size: `{file_size_mb:.1f} MB`"
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

# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start_health_server()
    logger.info("Starting FFmpeg Bot...")
    app.run()
