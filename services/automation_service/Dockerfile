FROM python:3.11-slim

WORKDIR /app
COPY services/automation_service/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY services/automation_service/ /app/
COPY shared/ /app/shared/

CMD ["python", "main.py"]
