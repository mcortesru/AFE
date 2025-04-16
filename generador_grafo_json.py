import os
import json
import fitz  # PyMuPDF
import spacy

# Cargar el modelo de NER de spaCy
nlp = spacy.load("en_core_web_md")

# Configurar las rutas
output_dir = "./jsons"

# Carpeta específica a procesar
folder_name = "AUPSA_ACE_JN_0062_001"
general_folder = "./AUPSA_ACE_JN_Correspondencia Presidencia/ACE_JN_62_001 a 62_004"
pdf_dir = os.path.join(general_folder, folder_name)

# Verificar que la carpeta existe
if not os.path.exists(pdf_dir):
    print(f"La carpeta {pdf_dir} no existe.")
    exit()

# Crear la carpeta de salida si no existe
os.makedirs(output_dir, exist_ok=True)

# Diccionario para almacenar la información extraída
data = {}

# Recorrer los archivos PDF en el directorio
for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_dir, filename)
        
        # Leer el contenido del PDF
        with fitz.open(pdf_path) as doc:
            text = "\n".join([page.get_text("text") for page in doc])
        
        # Procesar el texto con spaCy
        doc_nlp = nlp(text)

        # Calcular ruta relativa desde el directorio raíz
        root_dir = "AUPSA_ACE_JN_Correspondencia Presidencia"
        abs_root = os.path.abspath(root_dir)
        abs_pdf = os.path.abspath(pdf_path)
        relative_pdf_path = os.path.relpath(abs_pdf, abs_root)
        
        # Extraer entidades
        entities = {
            "dates": list(set(ent.text for ent in doc_nlp.ents if ent.label_ in ["DATE"])),
            "people": list(set(ent.text for ent in doc_nlp.ents if ent.label_ in ["PERSON"])),
            "locations": list(set(ent.text for ent in doc_nlp.ents if ent.label_ in ["GPE", "LOC"])),
            "organizations": list(set(ent.text for ent in doc_nlp.ents if ent.label_ in ["ORG"])),
            "creation_date": "",  # Campo vacío para rellenar manualmente
            "author": "",  # Nuevo campo vacío para el autor
            "pdf_path": relative_pdf_path
        }

        # Guardar en el diccionario con el nombre del archivo
        data[filename] = entities

# Nombre del archivo JSON de salida
output_path = os.path.join(output_dir, f"{folder_name}.json")

# Guardar los resultados en un JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Proceso completado. Datos guardados en {output_path}")
