import fitz  # Importa PyMuPDF
import re

FILE = './accionCatolica.pdf'

def extraer_texto_pdf(ruta_pdf=FILE):
    doc = fitz.open(ruta_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

def corregir_erratas_texto_language_tool_python(texto):
    import language_tool_python
    tool = language_tool_python.LanguageTool('es')
    matches = tool.check(texto)
    texto_corregido = language_tool_python.utils.correct(texto, matches)
    tool.close()
    return texto_corregido

def corregir_erratas_texto_pyspellchecker(texto):
    from spellchecker import SpellChecker
    spell = SpellChecker(language='es')
    palabras = re.split('(\W+)', texto)
    palabras_incorrectas = spell.unknown([palabra for palabra in palabras if palabra.strip() and palabra.isalpha()])
    texto_corregido = ''.join([spell.correction(palabra) if palabra in palabras_incorrectas and spell.correction(palabra) is not None else palabra for palabra in palabras])
    return texto_corregido

'''def corregir_erratas_texto_spacy(texto):
    import spacy
    nlp = spacy.load('es_core_news_sm')
    doc = nlp(texto)

    # Analizar el documento
    for token in doc:
    print(token.text, token.lemma_, token.pos_)'''

def dividir_texto(texto, longitud_maxima=1024):
    palabras = texto.split()
    segmentos = []
    segmento_actual = []
    longitud_actual = 0

    for palabra in palabras:
        segmento_actual.append(palabra)
        longitud_actual += len(palabra) + 1  # +1 por el espacio
        if longitud_actual >= longitud_maxima:
            segmentos.append(' '.join(segmento_actual))
            segmento_actual = []
            longitud_actual = 0

    # Añadir el último segmento si hay alguno
    if segmento_actual:
        segmentos.append(' '.join(segmento_actual))

    return segmentos

def extraer_texto_por_pagina (ruta_pdf=FILE):
    doc = fitz.open(ruta_pdf)
    texto_por_pagina = []
    for pagina in doc:
        texto = pagina.get_text("text").strip()
        texto_por_pagina.append(texto)
    doc.close()
    return texto_por_pagina

def quitar_guion_y_espacio(texto):
    texto_limpiado = re.sub(r'(\b-\s*|\s*-\s*)([^\W\d_])', r'\2', texto)
    return texto_limpiado
