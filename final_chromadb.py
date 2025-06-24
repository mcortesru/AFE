import os
import contextlib
import fitz
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Configuración
load_dotenv()
BASE_PATH = Path(__file__).resolve().parent / "AUPSA_ACE_JN_Correspondencia Presidencia"
CHROMA_DB_PATH = "./chroma_db_final"
COLLECTION_NAME = "coleccion_final"
CHUNK_SIZE = 500

# Modelo de embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

# Inicializar cliente
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Eliminar colección si ya existe
try:
    chroma_client.delete_collection(name=COLLECTION_NAME)
    print(f"[INFO] Colección '{COLLECTION_NAME}' eliminada.")
except Exception as e:
    print(f"[INFO] No se pudo eliminar la colección (posiblemente no existía): {e}")

# Crear nueva colección vacía
collection = chroma_client.create_collection(name=COLLECTION_NAME)
print(f"[INFO] Colección '{COLLECTION_NAME}' creada.")


# Supresión de logs de bajo nivel
@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, 'w') as devnull:
        old_stdout, old_stderr = os.dup(1), os.dup(2)
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(old_stdout, 1)
            os.dup2(old_stderr, 2)

# Extraer texto de PDF
def extraer_texto(path):
    with fitz.open(path) as doc:
        return "\n".join([page.get_text("text") for page in doc])

# Indexar todos los PDFs
def indexar_todos():
    pdfs = sorted(BASE_PATH.rglob("*.pdf"))
    if not pdfs:
        print("[ERROR] No se encontraron archivos PDF.")
        return

    print(f"[INFO] Encontrados {len(pdfs)} PDFs para indexar.")
    for pdf in pdfs:
        try:
            texto = extraer_texto(pdf)
            chunks = [texto[i:i + CHUNK_SIZE] for i in range(0, len(texto), CHUNK_SIZE)]

            for i, chunk in enumerate(chunks):
                vector = model.encode(chunk).tolist()
                doc_id = f"{pdf.stem}_chunk_{i}"
                collection.add(
                    documents=[chunk],
                    embeddings=[vector],
                    ids=[doc_id],
                    metadatas=[{
                        "name": pdf.name,
                        "path": str(pdf.relative_to(BASE_PATH))
                    }]
                )

            print(f"[✓] Indexado: {pdf.relative_to(BASE_PATH)} ({len(chunks)} fragmentos)")
        except Exception as e:
            print(f"[ERROR] {pdf.name}: {e}")


if __name__ == "__main__":
    print(f"[INFO] Iniciando indexación desde: {BASE_PATH}")
    #with suppress_output():
    indexar_todos()
    print("\n✅ Indexación completada.")
