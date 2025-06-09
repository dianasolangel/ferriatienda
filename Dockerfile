# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Evita problemas de input en contenedores
ENV PYTHONUNBUFFERED=1

# Variables de entorno para Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

# Instala curl y otras dependencias necesarias
RUN apt-get update && apt-get install -y curl build-essential && apt-get clean

# Instala Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Establece el directorio de trabajo
WORKDIR /app

# Copia primero los archivos de dependencias (mejor para cache)
COPY pyproject.toml poetry.lock ./

# Instala las dependencias del proyecto
RUN poetry install --no-root

# Copia el resto del proyecto
COPY . .

# Puerto expuesto (opcional si usas Streamlit)
EXPOSE 8501

# Comando por defecto (modifica según tu app principal)
CMD ["poetry", "run", "streamlit", "run", "ferriatienda/streamlit_app.py"]