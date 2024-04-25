import spacy
import mylib

def analizar_texto(texto):
    nlp = spacy.load("es_core_news_sm")
    doc = nlp(texto)
    entidades = []
    for ent in doc.ents:
        entidades.append((ent.text, ent.label_))
    return entidades

texto_pdf = mylib.extraer_texto_pdf()

entidades = analizar_texto(texto_pdf)

for texto, etiqueta in entidades:
    print(f"Entidad: {texto}, Categoría: {etiqueta}")
