# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Zagreb

WORKDIR /app

# build-deps za pymssql (freetds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    freetds-dev freetds-bin unixodbc-dev \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ako je repo root direktno u ovoj mapi, ostavi ovako;
# ako je sve unutar AlgebraAnalizaPodataka/, onda:
# COPY AlgebraAnalizaPodataka/ . 
COPY . .

# port na kojem služi Dash
EXPOSE 8050

# Gunicorn učitava Flask server objekt iz main.py (server = Flask(...))
CMD ["gunicorn", "main:server", "-b", "0.0.0.0:8050", "-w", "2", "--timeout", "120"]
