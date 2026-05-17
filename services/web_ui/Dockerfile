FROM python:3.11-slim
WORKDIR /app
COPY services/web_ui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/web_ui/ ./
CMD ["python", "main.py"]
