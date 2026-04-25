FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=prod

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        supervisor \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

COPY . .

RUN pip install --no-cache-dir -e .

RUN mkdir -p /var/log/supervisor /var/log/gunicorn

COPY deployment/supervisor/probotapi.conf /etc/supervisor/conf.d/probotapi.conf

EXPOSE 8000

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/probotapi.conf"]
