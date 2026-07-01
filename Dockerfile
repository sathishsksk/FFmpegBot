FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL source files (src/ and presets/ and everything else)
COPY src/ .
COPY presets/ ./presets/

# Temp directory for conversions
RUN mkdir -p /app/tmp

ENV PORT=8000
EXPOSE 8000

# Run from /app — all .py files are here directly
CMD ["python", "bot.py"]
