import os
import spacy
import fitz  # PyMuPDF para leer PDFs
import shutil
import subprocess
import json
import sys

# Configuración de directorios
DIRECTORIO_PDFS = "./Correspondencia/cartas_filtradas"
DIRECTORIO_PROCESADOS = "./Correspondencia/PDF_procesados"
DIRECTORIO_DATOS = "./Correspondencia/Datos_procesados"

os.makedirs(DIRECTORIO_PROCESADOS, exist_ok=True)
os.makedirs(DIRECTORIO_DATOS, exist_ok=True)

def extraer_texto_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    texto = "\n".join([page.get_text() for page in doc])
    return texto

def extraer_entidades(texto):
    nlp = spacy.load("es_core_news_sm")  # Modelo en español
    doc = nlp(texto)
    entidades = {
        "Person": set(),
        "Date": set(),
        "Location": set(),
        "Organization": set()
    }
    for ent in doc.ents:
        if ent.label_ in ["PER", "ORG", "LOC", "DATE"]:
            entidades[ent.label_.replace("PER", "Person").replace("ORG", "Organization").replace("LOC", "Location").replace("DATE", "Date")].add(ent.text)
    return entidades

def guardar_entidades_local(documento, entidades):
    """Guarda las entidades extraídas en un archivo JSON local."""
    ruta_salida = os.path.join(DIRECTORIO_DATOS, f"{documento}.json")

    # Convertir los conjuntos a listas para que sean serializables en JSON
    entidades_serializables = {tipo: list(valores) for tipo, valores in entidades.items()}

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(entidades_serializables, f, indent=4, ensure_ascii=False)

    print(f"✅ Entidades guardadas en {ruta_salida}")


def abrir_pdf(pdf_path):
    """Abrir el archivo PDF con el visor predeterminado del sistema"""
    try:
        if os.name == "nt":  # Windows
            os.startfile(pdf_path)
        elif os.name == "posix":  # macOS y Linux
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", pdf_path])
    except Exception as e:
        print(f"❌ No se pudo abrir el archivo {pdf_path}: {e}")

def mover_archivo(ruta_origen, ruta_destino):
    """Mover el archivo a la carpeta de procesados"""
    try:
        shutil.move(ruta_origen, ruta_destino)
        print(f"✅ Archivo movido a {ruta_destino}")
    except Exception as e:
        print(f"❌ Error al mover el archivo: {e}")

def procesar_directorio(directorio):
    archivos = [f for f in os.listdir(directorio) if f.endswith(".pdf")]
    
    for archivo in archivos:
        ruta = os.path.join(directorio, archivo)
        print(f"\n📄 Procesando: {archivo}")
        
        # Abrir el PDF en el visor predeterminado
        abrir_pdf(ruta)
        
        texto = extraer_texto_pdf(ruta)
        entidades = extraer_entidades(texto)
        
        # Mostrar entidades y permitir edición manual
        for tipo, valores in entidades.items():
            print(f"\n{tipo} encontrados:")
            for idx, valor in enumerate(valores, start=1):
                print(f"[{idx}] {valor}")
            
            # Permitir edición
            opcion = input(f"¿Quieres editar {tipo}? (s/n): ").strip().lower()
            if opcion == "s":
                nuevos_valores = input(f"Introduce {tipo} separados por comas: ").split(",")
                entidades[tipo] = set(v.strip() for v in nuevos_valores if v.strip())
        
        # Guardar localmente
        guardar_entidades_local(archivo, entidades)
        
        # Mover archivo procesado
        mover_archivo(ruta, os.path.join(DIRECTORIO_PROCESADOS, archivo))
        
        input("Presiona Enter para continuar con el siguiente documento...")

# Ejecutar el procesamiento
procesar_directorio(DIRECTORIO_PDFS)
