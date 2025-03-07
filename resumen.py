import json
import openai
import fitz
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Función para extraer texto de un PDF
def extraer_texto_pdf(ruta_pdf):
    doc = fitz.open(ruta_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

# Obtener la ruta del archivo PDF
if len(sys.argv) < 2:
    path_al_archivo = "/Users/administrador/Desktop/PDFs/Documentos/CARTAS/005-08-1-2.pdf"
else:
    path_al_archivo = sys.argv[1]

try:
    texto = extraer_texto_pdf(path_al_archivo)
except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)

# 📌 Construcción de la solicitud para ChatGPT
if OPENAI_API_KEY:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Puedes cambiar a gpt-3.5-turbo si lo prefieres
            messages=[
                {"role": "system", "content": "Resume el siguiente texto completo:"},
                {"role": "user", "content": texto},
            ],
            max_tokens=500,  # Ajusta la longitud del resumen
            temperature=0.3,
            top_p=0.9,
            frequency_penalty=0.5
        )
        resumen = response.choices[0].message.content.strip()
        print(resumen)
    except Exception as e:
        print(f"❌ Error con OpenAI: {e}")
else:
    print("⚠️ Error: No se encontró la clave de API de OpenAI.")
