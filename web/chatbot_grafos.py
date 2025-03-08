import os
import networkx as nx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import chromadb
import fitz
from pyvis.network import Network
import openai
from dotenv import load_dotenv
import spacy

# 📌 Cargar modelo de spaCy
nlp = spacy.load("es_core_news_sm")

# 📌 Cargar modelo de embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

# 📌 Configuración del entorno y OpenAI
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# 📌 Configuración de rutas y ChromaDB
RUTA_DOCUMENTOS = os.path.abspath("../Correspondencia/Cartas Manuel M. Pereiro")
CHROMA_DB_PATH = "chroma_db"
collection_name = "chatbot_collection"
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_or_create_collection(name=collection_name)

# 📌 Extraer entidades con spaCy
def extraer_entidades(texto):
    """Extrae nombres de personas, lugares, fechas y organizaciones del texto."""
    doc = nlp(texto)
    return {
        "personas": list({ent.text for ent in doc.ents if ent.label_ == "PER"}),
        "lugares": list({ent.text for ent in doc.ents if ent.label_ in ["LOC", "GPE"]}),
        "fechas": list({ent.text for ent in doc.ents if ent.label_ == "DATE"}),
        "organizaciones": list({ent.text for ent in doc.ents if ent.label_ == "ORG"}),
    }

# 📌 Extraer texto de PDFs
def extraer_texto_pdf(ruta_pdf):
    """Extrae texto de un archivo PDF."""
    doc = fitz.open(ruta_pdf)
    return "".join([pagina.get_text() for pagina in doc])

# 📌 Procesar documentos en ChromaDB
def procesar_documentos_en_carpeta(ruta_carpeta):
    """Procesa cada documento PDF y lo indexa en ChromaDB de manera independiente."""
    
    archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.endswith(".pdf")]
    if not archivos_pdf:
        print("[ERROR] No se encontraron documentos.")
        return False

    ids_existentes = set(collection.get()["ids"])  # Obtener IDs ya indexados
    contador = 0

    for archivo in archivos_pdf:
        contador += 1
        ruta_pdf = os.path.join(ruta_carpeta, archivo)
        print(f"[INFO] Procesando: {ruta_pdf}")

        try:
            texto_documento = extraer_texto_pdf(ruta_pdf)
        except Exception as e:
            print(f"[ERROR] No se pudo extraer texto de {ruta_pdf}: {e}")
            continue

        chunk_size = 500
        chunks = [texto_documento[i:i+chunk_size] for i in range(0, len(texto_documento), chunk_size)]

        for i, chunk in enumerate(chunks):
            id_chunk = f"{archivo}-chunk-{i}"
            if id_chunk in ids_existentes:
                continue  # Evita indexar documentos repetidos

            vector = model.encode(chunk).tolist()

            # 🔥 Asegurar que cada fragmento tiene su documento correctamente asignado
            if not archivo or not isinstance(archivo, str):
                archivo = "Desconocido"

            metadatas = [{"archivo": archivo}]

            # 🔍 Depuración para verificar qué metadatos se guardan
            print(f"[DEBUG] Indexando fragmento: {id_chunk} - Metadatos: {metadatas}")

            collection.add(
                embeddings=[vector], 
                documents=[chunk], 
                ids=[id_chunk],
                metadatas=metadatas  # Agrega el nombre del documento como metadato
            )

    docs = collection.get()
    archivos_unicos = set(meta["archivo"] for meta in docs.get("metadatas", []) if meta and "archivo" in meta)
    print(f"[DEBUG] Total de documentos únicos en ChromaDB: {len(archivos_unicos)}")
    print(f"[DEBUG] Lista de documentos únicos: {archivos_unicos}")


    return True



# 📌 Construcción del Grafo
G = nx.Graph()

def construir_grafo():
    """Construye un grafo combinando relaciones explícitas e implícitas."""
    global G
    G.clear()

    docs = collection.get()
    textos = docs.get("documents", [])
    ids = docs.get("ids", [])
    metadatas = docs.get("metadatas", [])

    if not textos:
        print("[ERROR] No hay documentos en ChromaDB.")
        return False

    # 📌 Crear diccionario de ID -> Documento
    id_a_documento = {
        id: meta.get("archivo", "Desconocido") for id, meta in zip(ids, metadatas) if meta
    }

    # 📌 Extraer entidades y vectores semánticos
    id_a_entidades = {id: extraer_entidades(texto) for id, texto in zip(ids, textos)}
    vectores = np.array([model.encode(texto) for texto in textos])

        # 📌 Añadir nodos con metadatos correctos
    for id, texto in zip(ids, textos):
        documento_original = id_a_documento.get(id, "Desconocido")
        G.add_node(id, contenido=texto, documento=documento_original)

    # 📌 Agregar entidades como nodos y conectar con los fragmentos
    for id, entidades in id_a_entidades.items():
        for entidad in entidades["personas"] + entidades["lugares"] + entidades["fechas"] + entidades["organizaciones"]:
            if entidad not in G:
                G.add_node(entidad, tipo="entidad")  # Agregar nodo solo si no existe
            G.add_edge(id, entidad, tipo="mención")  # Conectar documento con la entidad


    # 📌 Conectar por relaciones explícitas (NERs)
    for id1, entidades1 in id_a_entidades.items():
        for id2, entidades2 in id_a_entidades.items():
            if id1 != id2:
                interseccion = (
                    set(entidades1["personas"]) & set(entidades2["personas"]) |
                    set(entidades1["lugares"]) & set(entidades2["lugares"]) |
                    set(entidades1["fechas"]) & set(entidades2["fechas"]) |
                    set(entidades1["organizaciones"]) & set(entidades2["organizaciones"])
                )
                if interseccion:
                    G.add_edge(id1, id2, peso=len(interseccion), tipo="relacion_explicita")

    # 📌 Conectar por similitud semántica
    distancias = cosine_similarity(vectores)
    for i in range(len(textos)):
        for j in range(i + 1, len(textos)):
            if i != j:  # Evitar autoconexiones
                similitud = distancias[i, j]
                if similitud > 0.5:
                    G.add_edge(ids[i], ids[j], peso=similitud, tipo="similitud_semantica")

    # 🔍 Verificar cuántos documentos están correctamente representados en el grafo
    documentos_en_grafo = set(G.nodes[nodo]["documento"] for nodo in G.nodes if "documento" in G.nodes[nodo])
    
    print(f"[INFO] Grafo construido con {len(G.nodes)} nodos y {len(G.edges)} conexiones.")
    print(f"[DEBUG] Total de documentos representados en el grafo: {len(documentos_en_grafo)}")
    print(f"[DEBUG] Lista de documentos en el grafo: {documentos_en_grafo}")
    

    return True


def buscar_respuesta_grafo(pregunta):
    """Busca respuestas priorizando la similitud semántica sobre las relaciones explícitas (NERs)."""
    if len(G.nodes) == 0:
        print("[ERROR] El grafo está vacío.")
        return "No hay información en el grafo."

    # 📌 Extraer entidades mencionadas en la pregunta
    entidades_pregunta = extraer_entidades(pregunta)
    nombres_pregunta = (
        list(entidades_pregunta["personas"]) +
        list(entidades_pregunta["lugares"]) +
        list(entidades_pregunta["fechas"]) +
        list(entidades_pregunta["organizaciones"])
    )

    # 📌 Detectar si la pregunta menciona un documento específico
    docs = collection.get()
    archivos_unicos = set(meta["archivo"] for meta in docs.get("metadatas", []) if meta and "archivo" in meta)
    documentos_mencionados = [doc for doc in archivos_unicos if doc in pregunta]

    # 📌 Buscar conexiones explícitas en el grafo (NERs)
    nodos_relevantes_exp = set()
    for nombre in nombres_pregunta:
        if nombre in G:
            conexiones = list(G.neighbors(nombre))
            if len(conexiones) > 5:  # 🔹 Solo tomar los 5 más conectados si hay muchos
                conexiones = conexiones[:5]
            nodos_relevantes_exp.update(conexiones)
    
    # 📌 Buscar conexiones implícitas usando similitud semántica
    vector_pregunta = model.encode(pregunta)
    similitudes = {
        nodo: cosine_similarity([vector_pregunta], [model.encode(G.nodes[nodo]["contenido"])]).flatten()[0]
        for nodo in G.nodes if "contenido" in G.nodes[nodo]
    }
    
    # 📌 Seleccionar fragmentos dinámicamente basado en similitud
    umbral_similitud = 0.4  # 🔥 Umbral para considerar un fragmento relevante
    nodos_relevantes_sem = {nodo for nodo, sim in similitudes.items() if sim >= umbral_similitud}
    
    # 📌 Priorizar fragmentos de documentos mencionados en la pregunta
    nodos_documentos_mencionados = set()
    if documentos_mencionados:
        for nodo in G.nodes:
            if "documento" in G.nodes[nodo] and G.nodes[nodo]["documento"] in documentos_mencionados:
                nodos_documentos_mencionados.add(nodo)
    
    # 📌 Combinar métodos con prioridad en documentos mencionados
    nodos_finales = nodos_documentos_mencionados | nodos_relevantes_sem | (nodos_relevantes_exp & nodos_relevantes_sem)
    
    if not nodos_finales:
        return "No encontré información relevante para tu pregunta."
    
    # 📌 Obtener los documentos únicos y fragmentos relevantes
    contexto_por_documento = {}
    for nodo in nodos_finales:
        resultado = collection.get(ids=[nodo])
        metadatas = resultado.get("metadatas", [{}])[0]
        documento_original = metadatas.get("archivo", "Desconocido") if isinstance(metadatas, dict) else "Desconocido"

        if documento_original == "Desconocido":
            print(f"[WARNING] Fragmento sin documento detectado: {nodo}")
            continue

        if documento_original not in contexto_por_documento:
            contexto_por_documento[documento_original] = []
        contexto_por_documento[documento_original].append(G.nodes[nodo]["contenido"])

    # 📌 Construir respuesta
    contexto_final = ""
    for doc, fragmentos in contexto_por_documento.items():
        contexto_final += f"\n🔹 **Documento: {doc}**\n" + "\n".join(fragmentos) + "\n"

    print(f"[INFO] Contexto construido con {len(nodos_finales)} fragmentos de {len(contexto_por_documento)} documentos.")
    return generar_respuesta(contexto_final, pregunta)




def generar_respuesta(texto_relevante, pregunta):
    """Genera una respuesta basada en fragmentos de documentos o en OpenAI GPT-4o si está disponible."""
    
    # Si no tienes una clave de OpenAI, simplemente devuelve los textos relevantes encontrados.
    if not OPENAI_API_KEY:
        return texto_relevante

    print("[INFO] Generando respuesta con OpenAI...")

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente que responde preguntas con la información proporcionada. No inventes datos y responde de forma clara y precisa"},
                {"role": "user", "content": f"Documentos relevantes:\n{texto_relevante}\n\nPregunta: {pregunta}"}
            ]
        )

        return respuesta.choices[0].message.content  # Extrae la respuesta del modelo
    except Exception as e:
        print(f"[ERROR] OpenAI falló: {e}")
        return texto_relevante  # Devuelve el texto original si OpenAI falla

# 📌 Iniciar el chatbot
if __name__ == "__main__":
    if procesar_documentos_en_carpeta(RUTA_DOCUMENTOS):
        if construir_grafo():
            print("\n[INFO] Chatbot interactivo iniciado. Escribe 'salir' para terminar.")
            while True:
                pregunta = input("\nTú: ")
                if pregunta.lower() == "salir":
                    print("[INFO] Chatbot finalizado.")
                    break
                respuesta = buscar_respuesta_grafo(pregunta)
                print(f"Bot: {respuesta}")
