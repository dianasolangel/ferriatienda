# ---- BASE IMAGE ----
FROM python:3.11-slim

# ---- ENVIRONMENT VARIABLES ----
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="/opt/poetry/bin:/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"
# ---- SYSTEM DEPENDENCIES ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl build-essential git python3-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ---- INSTALL POETRY ----
RUN curl -sSL https://install.python-poetry.org | python3 -

# ---- SET WORKDIR ----
WORKDIR /app

# ---- COPY FILES ----
COPY pyproject.toml poetry.lock ./

# ---- INSTALL DEPENDENCIES ----
# RUN poetry lock 
RUN poetry install --no-root --no-interaction

# ---- COPY SOURCE CODE ----
COPY . .

# ---- EXPOSE PORT ----
EXPOSE 8501

# ---- RUN APP ----
CMD ["poetry", "run", "streamlit", "run", "ferriatienda/streamlit_app.py"]