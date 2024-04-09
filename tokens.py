import spacy
import mylib

# Asegúrate de haber instalado el modelo español con el comando:
# python -m spacy download es_core_news_sm

def analizar_texto(texto):
    # Cargar el modelo en español de Spacy
    nlp = spacy.load("es_core_news_sm")
    doc = nlp(texto)
    entidades = []
    for ent in doc.ents:
        # Aquí podrías filtrar por tipos específicos de entidades si lo deseas
        # Por ejemplo, si solo quieres personas y organizaciones, podrías hacer:
        # if ent.label_ in ["PER", "ORG"]:
        entidades.append((ent.text, ent.label_))
    return entidades

# Simulamos la extracción de texto de un PDF como una cadena de ejemplo
texto_pdf = mylib.extraer_texto_pdf()

# Analizar el texto extraído
entidades = analizar_texto(texto_pdf)

# Imprimir las entidades encontradas
for texto, etiqueta in entidades:
    print(f"Entidad: {texto}, Categoría: {etiqueta}")
