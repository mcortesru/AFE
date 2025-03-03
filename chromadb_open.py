import sys
import mylib
import chromadb
import os
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions
import openai

TMP_DIR = "/tmp"
PREGUNTA_FILE = os.path.join(TMP_DIR, "pregunta.txt")
RESPUESTA_FILE = os.path.join(TMP_DIR, "respuesta.txt")

# Configuración para usar nube si es necesario
USE_CLOUD = os.getenv("USE_CLOUD", "false").lower() == "true"
OPENAI_API_KEY = "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"
INDEX_NAME = "documentos"

print("[INFO] Iniciando ejecución del chatbot...")

# Extraer el texto del PDF
modo_flask = "--flask" in sys.argv
if not modo_flask:
    if len(sys.argv) < 2:
        path_al_archivo = "/Users/administrador/Desktop/PDFs/Documentos/ACTAS/004-07-89.pdf"
    else:
        path_al_archivo = sys.argv[1]
else:
    path_al_archivo = None

print("[INFO] Extrayendo texto del PDF...")
try:
    texto = mylib.extraer_texto_pdf(path_al_archivo)
    print("[INFO] Texto extraído correctamente.")
except Exception as e:
    print(f"[ERROR] Error al procesar el archivo: {e}")
    sys.exit(1)
###
### Dividir el texto en fragmentos (chunks)
def dividir_texto(texto, tamano=500):
    palabras = texto.split()
    return [" ".join(palabras[i:i + tamano]) for i in range(0, len(palabras), tamano)]

print("[INFO] Dividiendo el texto en fragmentos...")
chunks = dividir_texto(texto)
print(f"[INFO] Texto dividido en {len(chunks)} fragmentos.")

# Inicializar modelo de embeddings
print("[INFO] Cargando modelo de embeddings...")
model = SentenceTransformer("all-MiniLM-L6-v2")


print("[INFO] Usando ChromaDB local para almacenamiento...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("documentos")
for i, chunk in enumerate(chunks):
    vector = model.encode(chunk).tolist()
    collection.add(embeddings=[vector], documents=[chunk], ids=[str(i)])
print("[INFO] Documentos indexados en ChromaDB.")

###
### Función para buscar respuestas
def buscar_respuesta(pregunta):
    print("[INFO] Buscando respuesta para la pregunta...")
    vector_pregunta = model.encode(pregunta).tolist()
    
    resultados = collection.query(query_embeddings=[vector_pregunta], n_results=3)
    respuesta = "\n".join(resultados["documents"][0]) if resultados["documents"] else "No se encontraron respuestas."
    
    print("[INFO] Respuesta encontrada.")
    return respuesta

###
### Generar respuesta con OpenAI si está habilitado
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

###
### Chatbot interactivo
def chatbot_interactivo():
    print("[INFO] Chatbot de documentos iniciado. Escribe 'salir' para terminar.")
    while True:
        pregunta = input("Tú: ")
        if pregunta.lower() == "salir":
            print("[INFO] Chatbot finalizado.")
            break
        texto_relevante = buscar_respuesta(pregunta)
        respuesta = generar_respuesta(texto_relevante, pregunta)
        print(f"Bot: {respuesta}")

###
### Chatbot flask
def chatbot_flask():
    print("[INFO] Iniciando modo Flask...")

    # Verifica si el archivo de pregunta existe antes de leerlo
    if not os.path.exists(PREGUNTA_FILE):
        print("[ERROR] No se encontró el archivo de pregunta.")
        return
    
    with open(PREGUNTA_FILE, "r") as f:
        pregunta = f.read().strip()

    print(f"[INFO] Pregunta recibida: {pregunta}")
    
    texto_relevante = buscar_respuesta(pregunta)
    respuesta = generar_respuesta(texto_relevante, pregunta)
    
    with open(RESPUESTA_FILE, "w") as f:
        f.write(respuesta)

    print(f"[INFO] Respuesta guardada en {RESPUESTA_FILE}")

if __name__ == "__main__":
    if modo_flask:
        chatbot_flask()
    else:
        chatbot_interactivo()