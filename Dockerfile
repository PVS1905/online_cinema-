FROM python:3.10

# Встановлюємо змінні оточення
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off
ENV ALEMBIC_CONFIG=/usr/src/alembic/alembic.ini
ENV PYTHONPATH=/usr/src/fastapi

# Встановлюємо системні залежності
RUN apt update && apt install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    dos2unix \
    && apt clean

# Встановлюємо pip та Poetry
RUN python -m pip install --upgrade pip && \
    pip install poetry

# Копіюємо файли залежностей
COPY ./pyproject.toml ./poetry.lock /usr/src/poetry/
COPY ./alembic.ini /usr/src/alembic/alembic.ini

# Налаштовуємо Poetry
WORKDIR /usr/src/poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main --no-interaction

# Копіюємо вихідний код
WORKDIR /usr/src/fastapi
COPY ./src .

# Копіюємо скрипти та налаштовуємо їх
COPY ./commands /commands
RUN dos2unix /commands/*.sh && \
    chmod +x /commands/*.sh