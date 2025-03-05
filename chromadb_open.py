import os
import shutil
import logging
import chromadb
import argparse
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions
import openai
from flask_cors import CORS
import fitz
from dotenv import load_dotenv

def extraer_texto_pdf(ruta_pdf):
    doc = fitz.open(ruta_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

# Configuración del servidor Flask
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

# Cargar clave API de OpenAI desde variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
# Configuración de embeddings y base de datos

# Ruta por defecto si no se proporciona un documento
#DEFAULT_DOC_PATH = "/Users/administrador/Desktop/PDFs/Documentos/CARTAS/005-10-14-15.pdf"
DEFAULT_DOC_PATH = "/Users/administrador/Desktop/PDFs/Documentos/CUESTIONARIO/004-07-159.pdf"

CHROMA_DB_PATH = "./chroma_db"
collection_name = "chatbot_collection"
model = SentenceTransformer("all-MiniLM-L6-v2")
texto_documento = ""
global collection


# Iniciar cliente ChromaDB
print("[INFO] Iniciando conexión con ChromaDB...")

# **Eliminar la carpeta de la base de datos antes de crear una nueva**
def resetear_chromaDB():
    """ Elimina todos los archivos y directorios en la base de datos de ChromaDB y gestiona la colección. """
    # Verificar si existe la carpeta de la base de datos
    if os.path.exists(CHROMA_DB_PATH):
        # Recorremos todos los archivos y directorios en la carpeta
        for filename in os.listdir(CHROMA_DB_PATH):
            file_path = os.path.join(CHROMA_DB_PATH, filename)
            # Si es un archivo que no sea "chroma.sqlite3", eliminarlo
            if os.path.isfile(file_path) and filename != "chroma.sqlite3":
                os.remove(file_path)  # Eliminar archivo individual
                print(f"[INFO] Eliminado archivo: {file_path}")
            # Si es un directorio, eliminar el directorio y su contenido
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Eliminar directorio y su contenido
                print(f"[INFO] Eliminado directorio: {file_path}")
        
        print("[INFO] Archivos y directorios no deseados eliminados de ChromaDB.")
    else:
        print("[INFO] La carpeta de ChromaDB no existe.")
    
    # Crear un nuevo cliente de ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Intentamos eliminar la colección si existe
    try:
        chroma_client.delete_collection(name=collection_name)
        print("[INFO] Colección eliminada correctamente.")
    except Exception as e:
        print(f"[INFO] No se pudo eliminar la colección (posiblemente no existe): {e}")
    
    # Crear una nueva colección
    collection = chroma_client.create_collection(name=collection_name)
    print("[INFO] Nueva colección creada en ChromaDB.")
    
    return collection  # Retorna la colección


# Función para procesar un documento y almacenarlo en ChromaDB
def procesar_documento(path_al_archivo):
    """ Procesa un solo documento y lo indexa en ChromaDB. """
    global texto_documento, collection  # Asegúrate de que 'collection' es global
    print(f"[INFO] Procesando documento: {path_al_archivo}")

    if not os.path.exists(path_al_archivo):
        print(f"[ERROR] El archivo {path_al_archivo} no existe.")
        return False

    # Resetear la base de datos para asegurarnos de que solo hay un documento indexado
    collection = resetear_chromaDB()  # Asignar la colección aquí

    try:
        texto_documento = extraer_texto_pdf(path_al_archivo)
        print("[INFO] Texto extraído correctamente.")
    except Exception as e:
        print(f"[ERROR] Error al procesar el archivo {path_al_archivo}: {e}")
        return False

    # Dividir texto en fragmentos e indexarlos en ChromaDB
    chunk_size = 500
    chunks = [texto_documento[i:i+chunk_size] for i in range(0, len(texto_documento), chunk_size)]

    print("[INFO] Indexando el documento en ChromaDB...")
    for i, chunk in enumerate(chunks):
        vector = model.encode(chunk).tolist()
        collection.add(embeddings=[vector], documents=[chunk], ids=[str(i)])

    print("[INFO] Documento indexado correctamente en ChromaDB.")
    return True

# **Ruta para procesar documentos desde API**
@app.route("/procesar_documento", methods=["POST"])
def procesar_documento_api():
    data = request.json
    path_al_archivo = data.get("file_path")

    if not path_al_archivo:
        return jsonify({"error": "No se proporcionó la ruta del archivo"}), 400

    if procesar_documento(path_al_archivo):
        return jsonify({"message": "Documento procesado correctamente"})
    else:
        return jsonify({"error": "Error al procesar el documento"}), 500

# **Función para buscar respuestas en ChromaDB**
def buscar_respuesta(pregunta):
    print("[INFO] Buscando respuesta para la pregunta...")
    vector_pregunta = model.encode(pregunta).tolist()
    
    resultados = collection.query(query_embeddings=[vector_pregunta], n_results=3)
    respuesta = "\n".join(resultados["documents"][0]) if resultados["documents"] else "No se encontraron respuestas."
    
    print("[INFO] Respuesta encontrada.")
    return respuesta

# **Generar respuesta con OpenAI si está habilitado**
def generar_respuesta(texto_relevante, pregunta):
    if OPENAI_API_KEY:
        print("[INFO] Generando respuesta con OpenAI...")
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            respuesta = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Responde preguntas basadas en el documento proporcionado."},
                    {"role": "user", "content": f"Documento relevante:\n{texto_relevante}\n\nPregunta: {pregunta}"}
                ]
            )
            print("[INFO] Respuesta generada con OpenAI.")
            return respuesta.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] Error con OpenAI: {e}")
            return texto_relevante  # Fallback a ChromaDB
    return texto_relevante


def chatbot_inicializar(documento=None):
    """ Inicializa el chatbot con un documento. """
    if not documento:
        print(f"[INFO] No se proporcionó documento. Usando por defecto: {DEFAULT_DOC_PATH}")
        documento = DEFAULT_DOC_PATH

    if procesar_documento(documento):
        print("[INFO] Chatbot inicializado correctamente.")
        return True
    else:
        print("[ERROR] No se pudo procesar el documento.")
        return False

def chat(pregunta):
    """ Recibe una pregunta y devuelve una respuesta basada en el documento procesado. """
    if not pregunta.strip():
        return "Por favor, introduce una pregunta válida."
    
    texto_relevante = buscar_respuesta(pregunta)
    respuesta = generar_respuesta(texto_relevante, pregunta)
    return respuesta

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cargar documento en ChromaDB y ejecutar chatbot interactivo.")
    parser.add_argument("documento", nargs="?", help="Especificar documento")

    args = parser.parse_args()
    
    if chatbot_inicializar(args.documento):
        print("\n[INFO] Chatbot interactivo iniciado. Escribe 'salir' para terminar.")
        while True:
            pregunta = input("\nTú: ")
            if pregunta.lower() == "salir":
                print("[INFO] Chatbot finalizado.")
                break
            respuesta = chat(pregunta)
            print(f"Bot: {respuesta}")
