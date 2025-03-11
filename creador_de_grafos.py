from neo4j import GraphDatabase
import json
import os

# Configuración de Neo4j (local)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "tu_contraseña"

DIRECTORIO_DATOS = "./Correspondencia/Datos_procesados"

def conectar_neo4j():
    """Conecta con Neo4j y verifica la conexión"""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✅ Conexión exitosa con Neo4j local")
        return driver
    except Exception as e:
        print("❌ Error al conectar con Neo4j:", e)
        return None

def cargar_json_a_neo4j(driver):
    """Carga los archivos JSON a Neo4j"""
    archivos = [f for f in os.listdir(DIRECTORIO_DATOS) if f.endswith(".json")]
    
    with driver.session() as session:
        for archivo in archivos:
            ruta = os.path.join(DIRECTORIO_DATOS, archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)

            nombre_documento = archivo.replace(".json", "")

            # Crear nodo de documento
            session.run("MERGE (d:Document {name: $name})", name=nombre_documento)

            # Crear nodos de entidades y relaciones
            for tipo, valores in datos.items():
                for valor in valores:
                    session.run(f"""
                        MERGE (e:{tipo} {{name: $name}})
                        MERGE (e)-[:MENTIONED_IN]->(d:Document {{name: $doc}})
                    """, name=valor, doc=nombre_documento)

            print(f"✅ Cargado en Neo4j: {nombre_documento}")

def main():
    driver = conectar_neo4j()
    if driver:
        cargar_json_a_neo4j(driver)
        driver.close()

if __name__ == "__main__":
    main()
