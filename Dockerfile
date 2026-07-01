FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/

# Temp directory for conversions
RUN mkdir -p /app/tmp

ENV PORT=8000

EXPOSE 8000

WORKDIR /app/src

CMD ["python", "bot.py"]
