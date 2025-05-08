import spacy
import fitz
import os
from pathlib import Path
from neo4j import GraphDatabase
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables del entorno (.env)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

NEO4J_URI = os.getenv("NEO4J_URI") or "bolt://localhost:7690"
NEO4J_USER = os.getenv("NEO4J_USER") or "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
BASE_PATH = Path("AUPSA_ACE_JN_Correspondencia Presidencia")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

client = OpenAI()

# Cargar modelo NLP
nlp = spacy.load("es_core_news_md")

# Extraer persona de la pregunta
def extract_entities(pregunta):
    doc = nlp(pregunta)
    entidades = []
    for ent in doc.ents:
        if ent.label_ in ["PER", "LOC", "GPE", "ORG", "DATE"]:
            entidades.append((ent.text, ent.label_))
    return entidades


def label_to_neo4j(label):
    return {
        "PER": "Person",
        "ORG": "Organization",
        "LOC": "Location",
        "GPE": "Location",
        "DATE": "Date"
    }.get(label, None)

# Consultar documentos relacionados desde Neo4j
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

# Leer texto de los PDFs
def load_text_from_docs(docs_info):
    texts = []
    for name, rel_path in docs_info:
        full_path = BASE_PATH / Path(rel_path)
        print(f"[DEBUG] Buscando archivo: {full_path}")
        if not full_path.exists():
            print(f"[WARN] No se encontró el archivo: {full_path}")
            continue
        try:
            with fitz.open(str(full_path)) as doc:
                full_text = "\n".join([page.get_text("text") for page in doc])
                texts.append(full_text)
        except Exception as e:
            print(f"[ERROR] No se pudo abrir {full_path}: {e}")
    return texts

def generar_cypher(pregunta):
    system_prompt = """
Eres un experto en bases de datos Neo4j. Genera una consulta Cypher para responder la pregunta de un usuario.

Esquema:
- (:Document {name, creation_date, author, pdf_path})
  -[:MENTIONS]->(:Person {name})
  -[:MENTIONS]->(:Organization {name})
  -[:MENTIONS]->(:Location {name})
  -[:MENTIONS]->(:Date {name})

Devuelve SOLO la consulta Cypher que devuelva los documentos `d.name` y `d.pdf_path`. No pongas ```cypher ni ninguna marca de código.
"""
    user_prompt = f"Pregunta: {pregunta}"

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    cypher = response.choices[0].message.content.strip()

    # 💡 Eliminar posibles backticks por seguridad
    cypher = cypher.replace("```cypher", "").replace("```", "").strip()
    return cypher



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
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# 🧠 Ejecución principal
if __name__ == "__main__":
    pregunta = input("Introduce tu pregunta: ")
    
    # Estrategia 1: entidades con spaCy
    entidades = extract_entities(pregunta)
    print(f"\n🔍 Entidades detectadas con spaCy: {entidades}")
    
    documentos_spacy = find_documents_related_to_entities(entidades)
    print(f"📄 Documentos relacionados (spaCy): {documentos_spacy}")
    
    textos_spacy = load_text_from_docs(documentos_spacy)

    # Estrategia 2: generar Cypher con GPT
    cypher_query = generar_cypher(pregunta)
    print(f"\n📜 Cypher generado por GPT:\n{cypher_query}")

    documentos_cypher = []
    with driver.session() as session:
        result = session.run(cypher_query)
        documentos_cypher = [(record["d.name"], record["d.pdf_path"]) for record in result]

    print(f"📄 Documentos relacionados (Cypher GPT): {documentos_cypher}")
    
    textos_cypher = load_text_from_docs(documentos_cypher)

    # Generar respuestas
    if textos_spacy:
        respuesta_spacy = generate_answer(pregunta, "\n\n".join(textos_spacy))
        print("\n🧠 Respuesta usando spaCy:\n")
        print(respuesta_spacy)
    else:
        print("\n⚠️ No se encontraron documentos usando entidades con spaCy.")

    if textos_cypher:
        respuesta_cypher = generate_answer(pregunta, "\n\n".join(textos_cypher))
        print("\n🧠 Respuesta usando Cypher generado por GPT:\n")
        print(respuesta_cypher)
    else:
        print("\n⚠️ No se encontraron documentos usando Cypher generado por GPT.")

    driver.close()
