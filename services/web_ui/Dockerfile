FROM python:3.11-slim

WORKDIR /app
COPY services/web_ui/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY services/web_ui/ /app/
COPY shared/ /app/shared/

EXPOSE 8080
CMD ["python", "main.py"]
