import fitz  # Importa PyMuPDF
import language_tool_python

FILE = './accionCatolica.pdf'

def extraer_texto_pdf(ruta_pdf=FILE):
    doc = fitz.open(ruta_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

def corregir_erratas_texto(texto):
    tool = language_tool_python.LanguageTool('es')
    
    # Encuentra errores en el texto
    matches = tool.check(texto)

    # Aplica correcciones al texto
    texto_corregido = language_tool_python.utils.correct(texto, matches)

    return texto_corregido

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
