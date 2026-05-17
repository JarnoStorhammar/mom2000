FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake libopenblas-dev liblapack-dev \
    libx11-dev libgtk-3-dev libboost-all-dev v4l-utils libv4l-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/face_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/face_service/ ./
COPY shared/ ./shared/
CMD ["python", "main.py"]
