FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/vision_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/vision_service/ ./
COPY shared/ ./shared/
CMD ["python", "main.py"]
