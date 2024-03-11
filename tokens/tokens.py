import mylib
import spacy

# Cargar el modelo en español
nlp = spacy.load("es_core_news_sm")

def analizar_texto(texto):
    doc = nlp(texto)
    entidades = []
    for ent in doc.ents:
        # Filtrar y excluir entidades clasificadas como "MISC"
        if ent.label_ != "MISC":
            entidades.append((ent.text, ent.label_))
    return entidades


ruta_pdf = "accionCatolica.pdf"

# Extraer texto del PDF
texto_pdf = mylib.extraer_texto_pdf(ruta_pdf)

# Analizar el texto extraído
entidades = analizar_texto(texto_pdf)

# Imprimir las entidades encontradas
for texto, etiqueta in entidades:
    print(f"Entidad: {texto}, Categoría: {etiqueta}")