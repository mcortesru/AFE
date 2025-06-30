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
import re
import contextlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración inicial
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
BASE_PATH = Path(__file__).resolve().parent.parent / "AUPSA_ACE_JN_Correspondencia Presidencia"
CHROMA_DB_PATH = "./chroma_db_final"
COLLECTION_NAME = "coleccion_final"

model = SentenceTransformer("all-MiniLM-L6-v2")

# spaCy
nlp = spacy.load("es_core_news_md")

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI") or "bolt://localhost:7690"
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
def clean_name(text):
    return re.sub(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ]", "", text)

def extract_entities(pregunta):
    doc = nlp(pregunta)
    return [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PER", "LOC", "GPE", "ORG", "DATE"]]

def label_to_neo4j(label):
    return {
        "PER": "Person",
        "LOC": "Location",
        "GPE": "Location",
        "ORG": "Person"  # Tratas entidades como Persona jurídica (ej)
    }.get(label, None)


def find_documents_related_to_entities(entities):
    docs = set()
    with driver.session() as session:
        for name, label in entities:
            if label == "PER":
                name_cleaned = re.sub(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ]", "", name)
                name_parts = name_cleaned.split()
                condiciones = " AND ".join([
                    f'(toLower(COALESCE(p.name, "")) CONTAINS toLower("{part}") OR ' +
                    f'toLower(COALESCE(p.surname1, "")) CONTAINS toLower("{part}") OR ' +
                    f'toLower(COALESCE(p.surname2, "")) CONTAINS toLower("{part}"))'
                    for part in name_parts
                ])
                consulta = f"""
                MATCH (p:Person)-[:MENTIONED_IN]->(d:Document)
                WHERE {condiciones}
                RETURN DISTINCT d.file_name AS doc_name, d.relative_path AS pdf_path
                """
            else:
                neo4j_label = label_to_neo4j(label)
                if not neo4j_label:
                    continue
                consulta = f"""
                MATCH (d:Document)-[:LOCATED_AT]->(e:{neo4j_label})
                WHERE toLower(e.name) CONTAINS toLower("{name}")
                RETURN d.file_name AS doc_name, d.relative_path AS pdf_path
                """

            try:
                result = session.run(consulta)
                for record in result:
                    docs.add((record["doc_name"], record["pdf_path"]))
            except Exception as e:
                print(f"[⚠️] Error ejecutando consulta Cypher para '{name}': {e}")
    return list(docs)





def generar_cypher(pregunta):
    system_prompt = f"""
Eres un asistente experto en generar consultas Cypher para Neo4j.
Tu única tarea es, dada una pregunta en lenguaje natural, generar **una única consulta Cypher** que recupere los documentos históricos más relevantes.

⚠️ IMPORTANTE:
- Devuelve **SOLO la consulta Cypher**, sin explicaciones, sin encabezados ni formato Markdown.
- La consulta debe terminar siempre en:
  RETURN d.file_name, d.relative_path
- Nunca utilices más de una cláusula MATCH sin encadenarlas con WITH. Prefiere una única cláusula MATCH cuando sea posible.
- Usa siempre las funciones toLower(), CONTAINS y COALESCE() para asegurar coincidencias robustas y evitar errores por valores nulos.
- Si se busca por palabras clave (por ejemplo “crisis económica” o “junta nacional”), esas palabras deben buscarse tanto en el campo d.title como en d.summary.
  Para ello, cada palabra clave debe generar una cláusula como:
    (
      toLower(COALESCE(d.title, '')) CONTAINS 'palabra' OR
      toLower(COALESCE(d.summary, '')) CONTAINS 'palabra'
    )
  Y deben combinarse todas con AND si hay más de una.
- Evita usar igualdad exacta (=) en nombres o lugares: utiliza CONTAINS.
- Si necesitas acceder a propiedades de la relación MENTIONED_IN (como `category` o `role`), debes dar nombre a la relación en el MATCH: (p:Person)-[r:MENTIONED_IN]->(d:Document)
- Los nombres de personas pueden estar divididos entre name, surname1 y surname2, y a veces mal segmentados. Para asegurar coincidencias:
  → Si la pregunta incluye varias partes de un mismo nombre (por ejemplo: "Pilar Garaizabal Berasátegui"), combina todos los fragmentos en una sola cláusula `WHERE`, uniendo con `OR` las comparaciones sobre los campos name, surname1 y surname2.
- Si la pregunta incluye personas o cargos, filtra usando:
  MATCH (p:Person)-[r:MENTIONED_IN]->(d:Document)
  WHERE (
      toLower(COALESCE(p.name, '')) CONTAINS 'parte1' OR
      toLower(COALESCE(p.surname1, '')) CONTAINS 'parte1' OR
      toLower(COALESCE(p.surname2, '')) CONTAINS 'parte1' OR
      toLower(COALESCE(p.name, '')) CONTAINS 'parte2' OR
      toLower(COALESCE(p.surname1, '')) CONTAINS 'parte2' OR
      toLower(COALESCE(p.surname2, '')) CONTAINS 'parte2' OR
      ...
  )
  AND toLower(COALESCE(r.role, '')) CONTAINS 'rol'

ESTRUCTURA DEL GRAFO:

NODOS:
- (Document) {{ file_name, title, summary, sheet_number, issue_date, relative_path }}
- (Person) {{ name, surname1, surname2, person_type }}  # person_type = 'pe' o 'ej'
- (Location) {{ name }}
- (DocumentType) {{ name }}
- (Folder) {{ number }}
- (Box) {{ number }}

RELACIONES:
- (Person)-[:MENTIONED_IN {{ category, role }}]->(Document)
- (Document)-[:LOCATED_AT {{ category }}]->(Location)
- (Document)-[:HAS_TYPE]->(DocumentType)
- (Document)-[:IN_FOLDER]->(Folder)-[:BELONGS_TO]->(Box)

CATEGORÍAS COMUNES:
- MENTIONED_IN.category: 'au' (autor), 'de' (destinatario), 'ot' (otro)
- MENTIONED_IN.role: texto libre (ej: 'presidente', 'secretario')
- LOCATED_AT.category: 'em' (emisión), 're' (recepción), 'ot' (otro)

CREACIÓN DEL GRAFO:

- (box:Box {{number}}) y (folder:Folder {{number}}) conectados con [:BELONGS_TO]
- (d:Document {{file_name}}) tiene propiedades title, summary, sheet_number, issue_date, relative_path
- (d)-[:HAS_TYPE]->(dt:DocumentType {{name}})
- (d)-[:IN_FOLDER]->(folder)
- (p:Person {{name, surname1, surname2, person_type}}) relacionado con d vía [:MENTIONED_IN {{category, role}}]
- (l:Location {{name}}) relacionado con d vía [:LOCATED_AT {{category}}]


Pregunta:
{pregunta}

Cypher:
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Pregunta: {pregunta}"}
        ]
    )
    consulta = response.choices[0].message.content.strip()

    # 🧼 Extraer solo la consulta que comience con MATCH o similar
    consulta = response.choices[0].message.content.strip()

    # 🧼 Extraer solo la consulta que comience con MATCH o similar
    import re
    match = re.search(r"\b(MATCH|WITH|CALL)\b[\s\S]+", consulta)
    consulta = match.group(0).strip() if match else ""

    return consulta

def run_cypher(cypher):
    with driver.session() as session:
        result = session.run(cypher)
        # Usa los nombres exactos devueltos por Cypher y no añadas BASE_PATH aquí.
        return [(record["d.file_name"], record["d.relative_path"]) for record in result]



def load_text_from_docs(docs_info):
    texts = []
    for name, rel_path in docs_info:
        full_path = BASE_PATH / Path(rel_path)  # Ahora concatena BASE_PATH correctamente.

        if not full_path.exists():
            print(f"[⚠️] Archivo no encontrado: {full_path}")
            continue
        try:
            with fitz.open(str(full_path)) as doc:
                full_text = "\n".join([page.get_text("text") for page in doc])
                texts.append(full_text)
        except Exception as e:
            print(f"[ERROR] No se pudo abrir {full_path}: {e}")
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
IMPORTANTE:
- Todos los documentos son históricos, por lo general de la segunda mitad del siglo XX.
- Si en los documentos no se menciona explícitamente algo, no debes asumir nada que no esté.
- Si hay información no está presente, limítate a usar la información disponible sin inventar.

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
            # Extraer solo las rutas (ruta relativa a BASE_PATH)
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
        textos_finales = load_text_from_docs(list(documentos_usados))
        respuesta_final_combinada = generate_answer(pregunta, "\n".join(textos_finales)) if textos_finales else "⚠️ No se encontró contenido en ninguno de los métodos."

        print("=== RESPUESTA SPACY ===")
        print(f"[Documentos usados: {[name for name, _ in documentos_entidades]}]")
        print(respuesta_spacy)

        print("=== RESPUESTA CYPHER ===")
        print(f"[Documentos usados: {[name for name, _ in documentos_cypher]}]")
        print(f"[Consulta Cypher usada: {cypher}]")
        print(respuesta_cypher)

        print("=== RESPUESTA CHROMA ===")
        print(f"[Documentos usados: {[name for name, _ in fuentes_vectoriales]}]")
        print(respuesta_vectorial)

        print("=== RESPUESTA COMBINADA ===")
        print(f"[Documentos usados: {[name for name, _ in documentos_usados]}]")
        print(respuesta_final_combinada)