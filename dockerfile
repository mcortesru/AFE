# Usamos una imagen base de Python 3.10
FROM python:3.10-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Crear y activar el entorno virtual
RUN python -m venv /app/myenv
ENV PATH="/app/myenv/bin:$PATH"

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

RUN mkdir -p /app/.tmp
ENV TMPDIR=/app/.tmp

# Copiar el archivo de dependencias
COPY requirements.txt /app/requirements.txt

# Instalar dependencias en el entorno virtual
RUN /app/myenv/bin/pip install --upgrade pip
RUN /app/myenv/bin/pip install --no-cache-dir -r requirements.txt

# Descargar modelos de NLP en el entorno virtual
RUN /app/myenv/bin/python -m spacy download es_core_news_sm
RUN /app/myenv/bin/python -c "import nltk; nltk.download('stopwords')"

# Exponer el puerto 5000 para la aplicación Flask
EXPOSE 5000

# Usar el entorno virtual para ejecutar la aplicación Flask
CMD ["/app/myenv/bin/python", "web/app.py"]
