FROM python:3.11-slim
WORKDIR /app
COPY services/automation_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/automation_service/ ./
COPY shared/ ./shared/
CMD ["python", "main.py"]
