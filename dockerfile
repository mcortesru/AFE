# Usamos una imagen base de Python 3.10
FROM python:3.10-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Copiar solo los archivos necesarios
COPY web /app/web
COPY vectorizador.pkl /app/vectorizador.pkl
COPY resumen.py /app/resumen.py
COPY palabras.py /app/palabras.py
COPY NER.py /app/NER.py
COPY final_model.pkl /app/final_model.pkl
COPY clasificador.py /app/clasificador.py
COPY chromadb_open.py /app/chromadb_open.py

COPY final_model.pkl /app/final_model.pkl
COPY vectorizador.pkl /app/vectorizador.pkl

# COPY .env /app/.env

RUN mkdir -p /app/.tmp
ENV TMPDIR=/app/.tmp
ENV PATH="/root/.local/bin:${PATH}"

# Copiar el archivo de dependencias
COPY requirements.txt /app/requirements.txt

# Instalar las dependencias
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Borrar más adelante
RUN python -m spacy download es_core_news_sm

# Exponer el puerto que la app Flask estará utilizando
EXPOSE 5000

# Definir el comando para ejecutar la aplicación Flask usando el entorno virtual
CMD ["python", "web/app.py"]
