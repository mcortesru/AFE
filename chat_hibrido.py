import os
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

# Configuración inicial
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
BASE_PATH = Path("AUPSA_ACE_JN_Correspondencia Presidencia")
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

# ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_collection(name=COLLECTION_NAME)

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
    vector = model.encode(pregunta).tolist()
    with suppress_low_level_output():
        resultado = collection.query(query_embeddings=[vector], n_results=5)    
    docs = resultado["documents"][0] if resultado["documents"] else []
    sources = {m["source"] for m in resultado["metadatas"][0]} if resultado["metadatas"] else []
    return "\n".join(docs), sources

def generate_answer(question, documents_text):
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
    return response.choices[0].message.content


# --- Ejecución principal ---
if __name__ == "__main__":
    pregunta = input("❓ Introduce tu pregunta: ")

    # 🧠 Método 1: spaCy + Neo4j
    print("\n🔍 Buscando por entidades (spaCy + Neo4j)...")
    entidades = extract_entities(pregunta)
    documentos_entidades = find_documents_related_to_entities(entidades)
    textos_spacy = load_text_from_docs(documentos_entidades)
    if textos_spacy:
        respuesta_spacy = generate_answer(pregunta, "\n\n".join(textos_spacy))
    else:
        respuesta_spacy = "⚠️ No se encontraron documentos relevantes con spaCy."

    # 🧠 Método 2: Cypher generado por GPT
    print("\n📜 Generando consulta Cypher con GPT...")
    cypher = generar_cypher(pregunta)
    documentos_cypher = run_cypher(cypher)
    textos_cypher = load_text_from_docs(documentos_cypher)
    if textos_cypher:
        respuesta_cypher = generate_answer(pregunta, "\n\n".join(textos_cypher))
    else:
        respuesta_cypher = "⚠️ No se encontraron documentos relevantes con Cypher generado por GPT."

    # 🧠 Método 3: Vector search con ChromaDB
    print("\n📚 Buscando semánticamente con ChromaDB...")
    contexto_vectorial, fuentes_vectoriales = buscar_texto_relevante(pregunta)
    if contexto_vectorial.strip():
        respuesta_vectorial = generate_answer(pregunta, contexto_vectorial)
    else:
        respuesta_vectorial = "⚠️ No se encontraron documentos relevantes con ChromaDB."

    # 🧠 Método 4: Juntar todos los documentos
    documentos_usados_final = set()
    documentos_usados_final.update(documentos_entidades)
    documentos_usados_final.update(documentos_cypher)
    documentos_usados_final.update([(name, name) for name in fuentes_vectoriales])
    
    documentos_usados_dict = {}
    for nombre, ruta in documentos_usados_final:
        if nombre not in documentos_usados_dict:
            documentos_usados_dict[nombre] = ruta
    
    # 📄 Cargar textos desde los documentos combinados
    textos_combinados_final = load_text_from_docs(documentos_usados_dict.items())
    if textos_combinados_final:
        texto_final = "\n\n".join(textos_combinados_final)
        respuesta_final_combinada = generate_answer(pregunta, texto_final)
    else:
        respuesta_final_combinada = "⚠️ No se encontró contenido relevante en ninguno de los métodos."

    # 🔽 Mostrar resultados por método
    print("\n\n🧠 RESPUESTA spaCy + Neo4j:\n")
    print(respuesta_spacy)

    print("\n\n🧠 RESPUESTA Cypher generado por GPT:\n")
    print(respuesta_cypher)

    print("\n\n🧠 RESPUESTA Vectorial con ChromaDB:\n")
    print(respuesta_vectorial)

    print("\n\n🧠 RESPUESTA COMBINADA:\n")
    print(respuesta_final_combinada)

    print("\n📌 Info extra:")
    
    print(f"- Entidades detectadas: {entidades}")
    
    print("- Documentos spaCy:")
    for nombre, ruta in sorted(documentos_entidades):
        print(f"  - {nombre} ({ruta})")

    print("- Documentos Cypher:")
    for nombre, ruta in sorted(documentos_cypher):
        print(f"  - {nombre} ({ruta})")

    print("- Fuentes vectoriales:")
    for nombre in sorted(fuentes_vectoriales):
        print(f"  - {nombre} ({nombre})")

    print("- Documentos usados para la respuesta final:")
    for nombre, ruta in sorted(documentos_usados_dict.items()):
        print(f"  - {nombre} ({ruta})")



    driver.close()
