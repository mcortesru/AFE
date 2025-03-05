import sys
import mylib
import chromadb
import os
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions
import openai
from pinecone import Pinecone, ServerlessSpec

TMP_DIR = "./.tmp"
PREGUNTA_FILE = os.path.join(TMP_DIR, "pregunta.txt")
RESPUESTA_FILE = os.path.join(TMP_DIR, "respuesta.txt")

# Configuración para usar nube si es necesario
USE_CLOUD = os.getenv("USE_CLOUD", "false").lower() == "true"
OPENAI_API_KEY = "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"
PINECONE_API_KEY = "pcsk_3hrsSS_4wHGEjQFJdPZBdztChmutU3e4wDY4BYXK65B1SqmNHgemcXckVAkvrkhGqCpYm6"
PINECONE_ENV = "us-west1-gcp"
INDEX_NAME = "documentos"
index_name = "my-index"

pc = Pinecone(
    api_key = PINECONE_API_KEY
)

existing_indexes = pc.list_indexes().names()

# Check if the index already exists
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="euclidean",
        spec=ServerlessSpec(
            cloud="gcp-starter",  # Use 'gcp-starter' instead of 'gcp'
            region="us-east1"  # Keep 'us-east1' or check Pinecone's docs for the correct region
        )
    )

print(f"Index '{index_name}' is ready!")

print("[INFO] Iniciando ejecución del chatbot...")

# Extraer el texto del PDF
if len(sys.argv) < 2:
    path_al_archivo = "/Users/administrador/Desktop/PDFs/Documentos/ACTAS/004-07-89.pdf"
else:
    path_al_archivo = sys.argv[1]

print("[INFO] Extrayendo texto del PDF...")
try:
    texto = mylib.extraer_texto_pdf(path_al_archivo)
    print("[INFO] Texto extraído correctamente.")
except Exception as e:
    print(f"[ERROR] Error al procesar el archivo: {e}")
    sys.exit(1)

# Dividir el texto en fragmentos (chunks)
def dividir_texto(texto, tamano=500):
    palabras = texto.split()
    return [" ".join(palabras[i:i + tamano]) for i in range(0, len(palabras), tamano)]

print("[INFO] Dividiendo el texto en fragmentos...")
chunks = dividir_texto(texto)
print(f"[INFO] Texto dividido en {len(chunks)} fragmentos.")

# Inicializar modelo de embeddings
print("[INFO] Cargando modelo de embeddings...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("[INFO] Usando Pinecone para almacenamiento en la nube...")
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
if INDEX_NAME not in pinecone.list_indexes():
    pinecone.create_index(INDEX_NAME, dimension=384)
index = pinecone.Index(INDEX_NAME)

print("[INFO] Subiendo embeddings a Pinecone...")
for i, chunk in enumerate(chunks):
    vector = model.encode(chunk).tolist()
    index.upsert(vectors=[(str(i), vector)])
print("[INFO] Embeddings subidos correctamente.")


# Función para buscar respuestas
def buscar_respuesta(pregunta):
    print("[INFO] Buscando respuesta para la pregunta...")
    vector_pregunta = model.encode(pregunta).tolist()
    
    if USE_CLOUD and PINECONE_API_KEY:
        resultados = index.query(vector_pregunta, top_k=3, include_metadata=True)
        respuesta = "\n".join([res["metadata"]["text"] for res in resultados["matches"]])
    else:
        resultados = collection.query(query_embeddings=[vector_pregunta], n_results=3)
        respuesta = "\n".join(resultados["documents"][0])
    
    print("[INFO] Respuesta encontrada.")
    return respuesta

# Generar respuesta con OpenAI si está habilitado
def generar_respuesta(texto_relevante, pregunta):
    if OPENAI_API_KEY:
        print("[INFO] Generando respuesta con OpenAI...")
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
    return texto_relevante

# Chatbot interactivo
def chatbot():
    print("[INFO] Chatbot de documentos iniciado. Escribe 'salir' para terminar.")
    while True:
        pregunta = input("Tú: ")
        if pregunta.lower() == "salir":
            print("[INFO] Chatbot finalizado.")
            break
        texto_relevante = buscar_respuesta(pregunta)
        respuesta = generar_respuesta(texto_relevante, pregunta)
        print(f"Bot: {respuesta}")

if __name__ == "__main__":
    chatbot()