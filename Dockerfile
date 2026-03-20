FROM python:3.11-slim

# Installa Chrome e dipendenze (metodo moderno)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Aggiungi il repository di Chrome (metodo moderno senza apt-key)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Installa Chrome
RUN apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Installa le dipendenze Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice
COPY app.py .

# Crea directory per output
RUN mkdir -p /tmp/easyhits4u

# Esegui lo script
CMD ["python", "app.py"]
