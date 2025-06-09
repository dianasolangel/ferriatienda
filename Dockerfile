# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Evita problemas de input en contenedores
ENV PYTHONUNBUFFERED=1

# Instala curl y otras dependencias necesarias
RUN apt-get update && apt-get install -y curl build-essential && apt-get clean

# Instala Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Añade Poetry al PATH
ENV PATH="/root/.local/bin:$PATH"

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos del proyecto
COPY . .

# Instala las dependencias del proyecto
RUN poetry install --no-root

# Comando por defecto (modifica según tu app principal)
CMD ["poetry", "run", "streamlit", "run", "ferriatienda/streamlit_app.py"]