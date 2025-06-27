FROM python:3.10-alpine
#
## Налаштування середовища
#ENV PYTHONDONTWRITEBYTECODE=1
#ENV PYTHONUNBUFFERED=1
#ENV PYTHONPATH=/usr/src/fastapi/
#
#WORKDIR /usr/src/fastapi/celery
#
## Встановлення системних залежностей
#RUN apk add --no-cache \
#    python3 \
#    py3-pip \
#    libpq \
#    libffi-dev \
#    gcc \
#    musl-dev \
#    postgresql-dev
#
## Встановлення Python залежностей
#RUN pip install --no-cache-dir --upgrade pip && \
#    pip install --no-cache-dir \
#    celery[redis]==5.3.6 \
#    psycopg2-binary==2.9.9 \
#    sqlalchemy==2.0.25 \
#    email-validator==2.0.0 \
#    alembic==1.12.0
#
## Копіювання коду
#COPY . .
#
## Створення непривілейованого користувача
#RUN adduser -D -u 1000 worker && \
#    chown -R worker:worker /usr/src/fastapi
#USER worker
#
## Команда запуску
#CMD ["celery", "-A", "src.celery_app.worker", "worker", "--loglevel=info"]

#FROM alpine:3.18

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/usr/src/fastapi/

WORKDIR /usr/src/fastapi/celery

COPY pyproject.toml poetry.lock ./

RUN pip install poetry&& \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main --no-interaction



COPY . .

RUN adduser -D -u 1000 worker && \
    chown -R worker:worker /usr/src/fastapi
USER worker
