# ============================================
#   Dockerfile
#   Sistema de Gestión - Dirección General
#   Python 3.12 + Django 6.0 + Gunicorn
# ============================================

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

# Builder stage: compilar psycopg2 desde fuente + dependencias de imágenes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     DJANGO_SETTINGS_MODULE=core.settings     APP_HOME=/DATA/CIM5NV

WORKDIR $APP_HOME

# Runtime: solo librerías necesarias para ejecutar
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    libwebp7 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN mkdir -p /DATA/CIM5NV/media /DATA/CIM5NV/staticfiles /DATA/CIM5NV/logs /DATA/CIM5NV/data

# Copiar entrypoint a la raiz (única copia) y hacerlo ejecutable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
