import os
import sys
import spacy
import fitz
from pathlib import Path
from neo4j import GraphDatabase
import openai
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
import contextlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración inicial
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
BASE_PATH = Path(__file__).resolve().parent.parent / "AUPSA_ACE_JN_Correspondencia Presidencia"
CHROMA_DB_PATH = "./chroma_db_prueba"
COLLECTION_NAME = "coleccion_prueba"
model = SentenceTransformer("all-MiniLM-L6-v2")

# spaCy
nlp = spacy.load("es_core_news_md")

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI") or "bolt://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER") or "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Probar conexión con Neo4j
try:
    with driver.session() as session:
        session.run("RETURN 1")
    print("[OK] Conexión con Neo4j establecida")
except Exception as e:
    print(f"[ERROR] No se pudo conectar a Neo4j: {e}")
    sys.exit(1)


# ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
from chromadb.errors import InvalidCollectionException

try:
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    print(f"[OK] La colección '{COLLECTION_NAME}' existe")
except InvalidCollectionException:
    print(f"[ERROR] La colección '{COLLECTION_NAME}' no existe. Por favor, crea la base de datos con el script correspondiente.")
    sys.exit(1)

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

# --- Funciones ---
def extract_entities(pregunta):
    doc = nlp(pregunta)
    return [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PER", "LOC", "GPE", "ORG", "DATE"]]

def label_to_neo4j(label):
    return {
        "PER": "Person",
        "ORG": "Organization",
        "LOC": "Location",
        "GPE": "Location",
        "DATE": "Date"
    }.get(label, None)

def find_documents_related_to_entities(entities):
    docs = set()
    with driver.session() as session:
        for name, label in entities:
            neo4j_label = label_to_neo4j(label)
            if not neo4j_label:
                continue
            result = session.run(
                f"""
                MATCH (e:{neo4j_label} {{name: $name}})<-[:MENTIONS]-(d:Document)
                RETURN d.name AS doc_name, d.pdf_path AS pdf_path
                """,
                name=name
            )
            for record in result:
                docs.add((record["doc_name"], record["pdf_path"]))
    return list(docs)

def generar_cypher(pregunta):
    system_prompt = """
Eres un experto en bases de datos Neo4j. Genera una consulta Cypher para responder la pregunta de un usuario.

Esquema:
- (:Document {name, creation_date, author, pdf_path})
  -[:MENTIONS]->(:Person {name})
  -[:MENTIONS]->(:Organization {name})
  -[:MENTIONS]->(:Location {name})
  -[:MENTIONS]->(:Date {name})

Devuelve SOLO la consulta Cypher que devuelva los documentos `d.name` y `d.pdf_path`.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Pregunta: {pregunta}"}
        ]
    )
    return response.choices[0].message.content.strip().replace("```cypher", "").replace("```", "").strip()

def run_cypher(cypher):
    with driver.session() as session:
        result = session.run(cypher)
        return [(record["d.name"], record["d.pdf_path"]) for record in result]

def load_text_from_docs(docs_info):
    texts = []
    for name, rel_path in docs_info:
        full_path = BASE_PATH / Path(rel_path)

        if not full_path.exists():
            continue
        try:
            with fitz.open(str(full_path)) as doc:
                full_text = "\n".join([page.get_text("text") for page in doc])
                texts.append(full_text)
        except Exception:
            continue
    return texts

def buscar_texto_relevante(pregunta):
    print("[DEBUG] Iniciando búsqueda de texto relevante con ChromaDB...")
    vector = model.encode(pregunta).tolist()
    with suppress_low_level_output():
        print("[DEBUG] Ejecutando la consulta en ChromaDB...")
        resultado = collection.query(query_embeddings=[vector], n_results=5)
    print("[DEBUG] Resultado obtenido de ChromaDB.")  
    docs = resultado["documents"][0] if resultado["documents"] else []
    sources = set()
    for m in resultado["metadatas"][0]:
        nombre = m.get("name", "")
        ruta = m.get("path", "")
        if nombre and ruta:
            sources.add((nombre, ruta))
    return "\n".join(docs), sources

def generate_answer(question, documents_text):
    print("[DEBUG] Generando respuesta con OpenAI...")
    prompt = f"""
Responde a esta pregunta basada únicamente en los siguientes documentos históricos:

---- PREGUNTA ----
{question}

---- DOCUMENTOS ----
{documents_text[:3000]}

---- RESPUESTA ----
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    print(f"[DEBUG] Respuesta generada de cahtgpt generada")
    return response.choices[0].message.content


# --- Ejecución principal ---
if __name__ == "__main__":
    if len(sys.argv) == 2:
        pregunta = sys.argv[1]
        print(f"[DEBUG] Pregunta recibida: {pregunta}")
        
        try:
            entidades = extract_entities(pregunta)
            print(f"[DEBUG] Entidades extraídas: {entidades}")

            documentos_entidades = find_documents_related_to_entities(entidades)
            print(f"[DEBUG] Documentos relacionados a las entidades: {documentos_entidades}")

            textos_spacy = load_text_from_docs(documentos_entidades)
            print(f"[DEBUG] Textos cargados de spaCy: {len(textos_spacy)} textos")

            respuesta_spacy = generate_answer(pregunta, "\n\n".join(textos_spacy)) if textos_spacy else "⚠️ No se encontraron documentos relevantes con spaCy."
            print(f"[DEBUG] Respuesta de spaCy: {respuesta_spacy}")

            cypher = generar_cypher(pregunta)
            print(f"[DEBUG] Consulta Cypher generada: {cypher}")

            documentos_cypher = run_cypher(cypher)
            print(f"[DEBUG] Documentos de Cypher: {documentos_cypher}")

            textos_cypher = load_text_from_docs(documentos_cypher)
            print(f"[DEBUG] Textos cargados de Cypher: {len(textos_cypher)} textos")

            respuesta_cypher = generate_answer(pregunta, "\n\n".join(textos_cypher)) if textos_cypher else "⚠️ No se encontraron documentos relevantes con Cypher."
            print(f"[DEBUG] Respuesta de Cypher: {respuesta_cypher}")

            contexto_vectorial, fuentes_vectoriales = buscar_texto_relevante(pregunta)
            print(f"[DEBUG] Resultados de ChromaDB: {contexto_vectorial}")

            respuesta_vectorial = generate_answer(pregunta, contexto_vectorial) if contexto_vectorial.strip() else "⚠️ No se encontraron documentos con ChromaDB."
            print(f"[DEBUG] Respuesta de ChromaDB: {respuesta_vectorial}")

            documentos_usados = set()
            documentos_usados.update(documentos_entidades)
            documentos_usados.update(documentos_cypher)
            documentos_usados.update(fuentes_vectoriales)
            textos_finales = load_text_from_docs(documentos_usados)
            print(f"[DEBUG] Textos finales: {len(textos_finales)} textos")

            respuesta_final_combinada = generate_answer(pregunta, "\n".join(textos_finales)) if textos_finales else "⚠️ No se encontró contenido en ninguno de los métodos."
            print(f"[DEBUG] Respuesta final combinada: {respuesta_final_combinada}")

        except Exception as e:
            print(f"[ERROR] Se produjo un error: {e}")

        pregunta = sys.argv[1]
        # Ejecutar procesamiento único sin bucle interactivo
        entidades = extract_entities(pregunta)
        documentos_entidades = find_documents_related_to_entities(entidades)
        textos_spacy = load_text_from_docs(documentos_entidades)
        respuesta_spacy = generate_answer(pregunta, "\n\n".join(textos_spacy)) if textos_spacy else "⚠️ No se encontraron documentos relevantes con spaCy."

        cypher = generar_cypher(pregunta)
        documentos_cypher = run_cypher(cypher)
        textos_cypher = load_text_from_docs(documentos_cypher)
        respuesta_cypher = generate_answer(pregunta, "\n\n".join(textos_cypher)) if textos_cypher else "⚠️ No se encontraron documentos relevantes con Cypher."

        contexto_vectorial, fuentes_vectoriales = buscar_texto_relevante(pregunta)
        respuesta_vectorial = generate_answer(pregunta, contexto_vectorial) if contexto_vectorial.strip() else "⚠️ No se encontraron documentos con ChromaDB."

        documentos_usados = set()
        documentos_usados.update(documentos_entidades)
        documentos_usados.update(documentos_cypher)
        documentos_usados.update(fuentes_vectoriales)
        textos_finales = load_text_from_docs(documentos_usados)
        respuesta_final_combinada = generate_answer(pregunta, "\n".join(textos_finales)) if textos_finales else "⚠️ No se encontró contenido en ninguno de los métodos."

        print("=== RESPUESTA SPACY ===")
        print(f"[Documentos usados: {[name for name, _ in documentos_entidades]}]")
        print(respuesta_spacy)

        print("=== RESPUESTA CYPHER ===")
        print(f"[Documentos usados: {[name for name, _ in documentos_cypher]}]")
        print(respuesta_cypher)

        print("=== RESPUESTA CHROMA ===")
        print(f"[Documentos usados: {[name for name, _ in fuentes_vectoriales]}]")
        print(respuesta_vectorial)

        print("=== RESPUESTA COMBINADA ===")
        print(f"[Documentos usados: {[name for name, _ in documentos_usados]}]")
        print(respuesta_final_combinada)


