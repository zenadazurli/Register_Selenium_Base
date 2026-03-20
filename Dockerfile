FROM python:3.11-slim

WORKDIR /app

# Copia e installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia i file dell'applicazione
COPY app.py .
COPY register_config.json .

# Crea directory per output
RUN mkdir -p /tmp/easyhits4u

# Esegui lo script
CMD ["python", "app.py"]
