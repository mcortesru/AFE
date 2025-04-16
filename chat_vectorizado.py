import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import contextlib
import logging
import fitz
import logging
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Config
load_dotenv()
BASE_DIR = Path("AUPSA_ACE_JN_Correspondencia Presidencia/ACE_JN_62_001 a 62_004/AUPSA_ACE_JN_0062_001")
CHROMA_DB_PATH = "./chroma_db_prueba"
COLLECTION_NAME = "coleccion_prueba"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Inicializar Chroma
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

@contextlib.contextmanager
def suppress_low_level_output():
    with open(os.devnull, 'w') as devnull:
        # Guarda los descriptores originales
        old_stdout_fd = os.dup(1)
        old_stderr_fd = os.dup(2)

        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)


# Extraer texto de PDF
def extraer_texto_pdf(path):
    with fitz.open(path) as doc:
        return "\n".join([page.get_text("text") for page in doc])

# Indexar todos los PDFs
def indexar_todos_los_pdfs():
    print("[INFO] Indexando todos los PDFs...")
    chunk_size = 500
    for ruta_pdf in BASE_DIR.rglob("*.pdf"):
        try:
            texto = extraer_texto_pdf(ruta_pdf)
            chunks = [texto[i:i+chunk_size] for i in range(0, len(texto), chunk_size)]
            for i, chunk in enumerate(chunks):
                vector = model.encode(chunk).tolist()
                doc_id = f"{os.path.basename(ruta_pdf)}_chunk_{i}"
                collection.add(
                    embeddings=[vector],
                    documents=[chunk],
                    ids=[doc_id],
                    metadatas=[{"source": str(ruta_pdf.relative_to(BASE_DIR.parent))}]
                )
            print(f"[✓] Indexado: {ruta_pdf}")
        except Exception as e:
            print(f"[ERROR] {ruta_pdf}: {e}")

# Buscar texto relevante
def buscar_texto_relevante(pregunta):
    vector = model.encode(pregunta).tolist()
    with suppress_low_level_output():
        resultado = collection.query(query_embeddings=[vector], n_results=5)
    docs = resultado["documents"][0] if resultado["documents"] else []
    sources = {m["source"] for m in resultado["metadatas"][0]} if resultado["metadatas"] else []
    return "\n".join(docs), sources


# Generar respuesta con OpenAI
def generar_respuesta(pregunta, contexto):
    mensajes = [
        {"role": "system", "content": "Responde en base a los siguientes documentos históricos."},
        {"role": "user", "content": f"{contexto}\n\nPregunta: {pregunta}"}
    ]
    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes
    )
    return respuesta.choices[0].message.content


# Intentar recuperar colección existente
coleccion_nueva = False
try:
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    print(f"[INFO] Colección '{COLLECTION_NAME}' existente cargada.")
except:
    print(f"[INFO] Colección '{COLLECTION_NAME}' no existe. Creándola e indexando los PDFs...")
    collection = chroma_client.create_collection(name=COLLECTION_NAME)
    coleccion_nueva = True
    indexar_todos_los_pdfs()

if __name__ == "__main__":
    if coleccion_nueva:
        print("\n✅ Indexación inicial completada.")
    print("\n🧠 Chatbot histórico listo. Escribe 'salir' para terminar.")
    while True:
        pregunta = input("\nTú: ")
        if pregunta.lower() == "salir":
            break
        contexto, fuentes = buscar_texto_relevante(pregunta)
        respuesta = generar_respuesta(pregunta, contexto)
        print(f"\nBot: {respuesta}")
        print(f"\n📁 Basado en documentos: {', '.join(fuentes)}")
