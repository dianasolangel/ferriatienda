# ---- BASE IMAGE ----
FROM python:3.11-slim

# ---- ENVIRONMENT VARIABLES ----
ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/poetry/bin:/app/.venv/bin:$PATH"

# ---- SYSTEM DEPENDENCIES ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl build-essential git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ---- INSTALL POETRY ----
RUN curl -sSL https://install.python-poetry.org | python3 -

# ---- SET WORKDIR ----
WORKDIR /app

# ---- COPY DEPENDENCY FILES ----
COPY pyproject.toml poetry.lock ./

# ---- INSTALL DEPENDENCIES ----
RUN poetry install --no-root

# ---- COPY THE REST OF THE PROJECT ----
COPY . .

# ---- EXPOSE STREAMLIT PORT ----
EXPOSE 8501

# ---- DEFAULT COMMAND ----
CMD ["poetry", "run", "streamlit", "run", "ferriatienda/streamlit_app.py"]