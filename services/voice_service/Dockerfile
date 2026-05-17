FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev pulseaudio-utils alsa-utils curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/voice_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN curl -L https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz \
    | tar xz -C /tmp && mv /tmp/piper/piper /usr/local/bin/piper
COPY services/voice_service/ ./
COPY shared/ ./shared/
CMD ["python", "main.py"]
