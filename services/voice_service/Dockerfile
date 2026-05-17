FROM python:3.11-slim

# PulseAudio client libs + audio tools
RUN apt-get update && apt-get install -y --no-install-recommends     pulseaudio-utils libpulse0 libsndfile1 portaudio19-dev     wget ca-certificates     && rm -rf /var/lib/apt/lists/*

# Install Piper TTS binary
RUN wget -q https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz     -O /tmp/piper.tar.gz     && tar -xzf /tmp/piper.tar.gz -C /usr/local/bin --strip-components=1     && rm /tmp/piper.tar.gz

WORKDIR /app
COPY services/voice_service/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY services/voice_service/ /app/
COPY shared/ /app/shared/

CMD ["python", "main.py"]
