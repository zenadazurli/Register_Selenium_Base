FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY register_config.json .

RUN mkdir -p /tmp/easyhits4u

CMD ["python", "app.py"]
