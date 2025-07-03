from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# ==========================
# 🔧 Conexión a Neo4j
# ==========================
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7690")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
BASE_DIR = Path("AUPSA_ACE_JN_Correspondencia Presidencia")


# ==========================
# 🧠 Crear nodos y relaciones
# ==========================
def create_nodes_and_relationships(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    with driver.session() as session:
        for pdf, details in data.items():
            pdf_path = details.get("pdf_path", "")
            full_path = BASE_DIR / Path(pdf_path)

            # Validar que el archivo exista
            if not full_path.exists():
                raise FileNotFoundError(f"❌ No se encontró el archivo PDF: {full_path}")

            # Crear nodo del documento
            session.run(
                """
                MERGE (d:Document {name: $pdf})
                SET d.creation_date = $creation_date,
                    d.author = $author,
                    d.pdf_path = $pdf_path
                """,
                pdf=pdf,
                creation_date=details.get("creation_date", ""),
                author=details.get("author", ""),
                pdf_path=pdf_path
            )

            # Crear entidades relacionadas
            label_map = {
                "dates": "Date",
                "people": "Person",
                "locations": "Location",
                "organizations": "Organization"
            }

            for category in details:
                if category not in label_map:
                    print(f"⚠️ Categoría no reconocida: {category}")
                    continue

                label = label_map[category]

                for item in details[category]:
                    if not isinstance(item, str) or not item.strip():
                        continue
                    session.run(
                        f"""
                        MATCH (d:Document {{name: $pdf}})
                        MERGE (n:{label} {{name: $item}})
                        MERGE (d)-[:MENTIONS]->(n)
                        """,
                        pdf=pdf,
                        item=item.strip()
                    )


# ==========================
# ▶️ Ejecutar
# ==========================
def main():
    json_path = "jsons/AUPSA_ACE_JN_0062_001.json"
    create_nodes_and_relationships(json_path)
    print("✅ Datos cargados en Neo4j correctamente.")

if __name__ == "__main__":
    main()
    driver.close()
