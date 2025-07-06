from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# ==========================
# 🔧 Conexión a Neo4j (local o AuraDB)
# ==========================
load_dotenv()
mode = os.getenv("NEO4J_MODE", "local")

if mode == "remote":
    NEO4J_URI = os.getenv("NEO4J_URI_REMOTE")
    NEO4J_USER = os.getenv("NEO4J_USER_REMOTE", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD_REMOTE")
else:
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7690")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Verificar conexión
with driver.session() as session:
    result = session.run("RETURN '✅ Conectado correctamente a Neo4j' AS mensaje")
    print(result.single()["mensaje"])

# ==========================
# 📂 Cargar JSON
# ==========================
JSON_PATH = Path("dbV0.json")
with open(JSON_PATH, "r", encoding="utf-8") as f:
    documentos = json.load(f)

# ==========================
# 📆 Validación segura de fechas
# ==========================
def safe_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
    except Exception:
        return "1900-01-01"

# ==========================
# 🧠 Función de importación
# ==========================
def crear_grafo(tx, doc):
    tx.run("""
        MERGE (box:Box {number: $box})
        MERGE (folder:Folder {number: $folder})
        MERGE (folder)-[:BELONGS_TO]->(box)
    """, box=doc["box"], folder=doc["folder"])

    tx.run("""
        MERGE (dt:DocumentType {name: $doc_type})
    """, doc_type=doc["document_type"])

    tx.run("""
        MATCH (folder:Folder {number: $folder})
        MATCH (dt:DocumentType {name: $doc_type})
        MERGE (d:Document {file_name: $file_name})
        SET d.title = $title,
            d.summary = $summary,
            d.sheet_number = $sheet_number,
            d.issue_date = date($issue_date),
            d.relative_path = $relative_path
        MERGE (d)-[:IN_FOLDER]->(folder)
        MERGE (d)-[:HAS_TYPE]->(dt)
    """, 
        file_name=doc["file_name"],
        title=doc["title"],
        summary=doc["summary"],
        sheet_number=str(doc.get("sheet_number", "")),
        issue_date=safe_date(doc.get("issue_date", "1900-01-01")),
        relative_path=doc.get("relative_path", ""),
        folder=doc["folder"],
        doc_type=doc["document_type"]
    )

    for person in doc.get("people", []):
        name = person.get("name")
        if not name:
            continue
        tx.run("""
            MERGE (p:Person {name: $name, person_type: $person_type})
            SET p.surname1 = $surname1,
                p.surname2 = $surname2
            WITH p
            MATCH (d:Document {file_name: $file_name})
            MERGE (p)-[:MENTIONED_IN {
                category: $category,
                role: $role
            }]->(d)
        """, 
            name=name,
            surname1=person.get("surname1") or "",
            surname2=person.get("surname2") or "",
            person_type=person.get("person_type", "pe"),
            category=person.get("category", "ot"),
            role=person.get("role") or "",
            file_name=doc["file_name"]
        )

    for loc in doc.get("locations", []):
        name = loc.get("name")
        if not name:
            continue
        tx.run("""
            MERGE (l:Location {name: $name})
            WITH l
            MATCH (d:Document {file_name: $file_name})
            MERGE (d)-[:LOCATED_AT {category: $category}]->(l)
        """,
            name=name,
            category=loc.get("category", "ot"),
            file_name=doc["file_name"]
        )

# ==========================
# ▶️ Ejecutar importación
# ==========================
with driver.session() as session:
    confirm = input(f"\n⚠️ Estás en modo '{mode}'. ¿Quieres borrar todos los datos existentes? (s/n): ").strip().lower()
    if confirm == "s":
        session.run("MATCH (n) DETACH DELETE n")
        print("[INFO] Base de datos limpiada.")

    for i, doc in enumerate(documentos):
        try:
            session.execute_write(crear_grafo, doc)
            print(f"[{i+1}/{len(documentos)}] Documento importado: {doc['file_name']}")
        except Exception as e:
            print(f"[{i+1}/{len(documentos)}] ❌ ERROR: {doc['file_name']} → {e}")

print("\n✅ Importación completa.")
