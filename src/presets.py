# Ready-to-use FFmpeg presets
# Key = command user types, Value = ffmpeg arguments (no "ffmpeg" at start)

PRESETS = {
    "hevc10": {
        "desc": "Convert video → HEVC H.265 10-bit 1080p (best quality)",
        "cmd": "-i {input} -vf scale=-2:1080 -c:v libx265 -crf 28 -preset medium -profile:v main10 -pix_fmt yuv420p10le -c:a copy {output}.mkv",
        "ext": ".mkv",
    },
    "hevc": {
        "desc": "Convert video → HEVC H.265 8-bit 1080p",
        "cmd": "-i {input} -vf scale=-2:1080 -c:v libx265 -crf 28 -preset medium -c:a copy {output}.mkv",
        "ext": ".mkv",
    },
    "h264": {
        "desc": "Convert video → H.264 1080p (widely compatible)",
        "cmd": "-i {input} -vf scale=-2:1080 -c:v libx264 -crf 23 -preset medium -c:a copy {output}.mp4",
        "ext": ".mp4",
    },
    "compress": {
        "desc": "Compress video (smaller file size, H.264)",
        "cmd": "-i {input} -c:v libx264 -crf 32 -preset slow -vf scale=-2:720 -c:a aac -b:a 128k {output}.mp4",
        "ext": ".mp4",
    },
    "mp3": {
        "desc": "Extract audio → MP3 320kbps",
        "cmd": "-i {input} -vn -c:a libmp3lame -q:a 0 {output}.mp3",
        "ext": ".mp3",
    },
    "m4a": {
        "desc": "Extract audio → M4A (AAC best quality)",
        "cmd": "-i {input} -vn -c:a aac -b:a 320k {output}.m4a",
        "ext": ".m4a",
    },
    "720p": {
        "desc": "Resize video → 720p H.264",
        "cmd": "-i {input} -vf scale=-2:720 -c:v libx264 -crf 23 -preset medium -c:a copy {output}.mp4",
        "ext": ".mp4",
    },
    "480p": {
        "desc": "Resize video → 480p H.264",
        "cmd": "-i {input} -vf scale=-2:480 -c:v libx264 -crf 23 -preset medium -c:a copy {output}.mp4",
        "ext": ".mp4",
    },
    "trim": {
        "desc": "Trim video (first 60 seconds) — edit cmd for custom time",
        "cmd": "-i {input} -ss 00:00:00 -t 00:01:00 -c copy {output}.mkv",
        "ext": ".mkv",
    },
}
