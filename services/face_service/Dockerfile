FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential cmake libopenblas-dev liblapack-dev     libx11-dev libgtk-3-dev libboost-python-dev     libv4l-dev v4l-utils     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY services/face_service/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY services/face_service/ /app/
COPY shared/ /app/shared/

CMD ["python", "main.py"]
