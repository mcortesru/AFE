import spacy
import mylib

# Cargar el modelo preentrenado de spaCy
nlp = spacy.load("en_core_web_sm")  # Asegúrate de descargar el modelo correcto para español

texto = mylib.extraer_texto_pdf('./circulares bis/004-07.pdf')

# Procesar el texto
doc = nlp(texto)

# Extraer entidades que son fechas
fechas = [ent for ent in doc.ents if ent.label_ == "DATE"]

# Imprimir las fechas encontradas
for fecha in fechas:
    print(fecha.text)
