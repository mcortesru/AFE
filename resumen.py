import json
from llamaapi import LlamaAPI
import requests
import sys

import fitz

def extraer_texto_pdf(ruta_pdf):
    doc = fitz.open(ruta_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

if len(sys.argv) < 2:
    # path_al_archivo = input("No se ha proporcionado el path del archivo. Por favor, introduce el path del archivo: ")   
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-147.pdf" 
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-68-69.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-71.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/005-11-30-33.pdf"  # MUY LARGO
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-165-168.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-155.pdf"
   path_al_archivo = "/Users/administrador/Desktop/PDFs/CUESTIONARIO/PRUEBAS/ACE_JAC_5A_01-25.pdf"
   path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-89.pdf"
   path_al_archivo = "/Users/administrador/Desktop/PDFs/Documentos/CARTAS/005-08-1-2.pdf"

else:
    path_al_archivo = sys.argv[1]

try:
    texto = extraer_texto_pdf(path_al_archivo)
except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)

# 📌 Inicializar LlamaAPI
api_token = "LL-Z8mrEuQPmlMauJWuXwIDlnoi9bFiSlFqiYQSx8E3lEfEleU7Zt5YB3qGUgeKOf2e"
llama = LlamaAPI(api_token)

# 📌 Construcción de la solicitud
api_request_json = {
    "model": "llama3.1-70b",
    "messages": [
        {"role": "system", "content": "Resume el siguiente texto completo brevemente:"},
        {"role": "user", "content": texto},
    ],
    "max_token": 500,  # Asegura que el resumen pueda ser más largo si es necesario
    "temperature": 0.3,  # Reduce la creatividad para obtener un resumen más preciso
    "top_p": 0.9,  # Mantiene coherencia en la respuesta
    "frequency_penalty": 0.5,  # Evita repeticiones innecesarias
    "stream": False
}

# 📌 Hacer la solicitud y obtener solo el resumen
try:
    response = llama.run(api_request_json)
    response_json = response.json()

    # 📌 Extraer solo el contenido del resumen
    if isinstance(response_json, dict) and "choices" in response_json:
        choices = response_json["choices"]
        if isinstance(choices, list) and len(choices) > 0 and "message" in choices[0]:
            content = choices[0]["message"].get("content", "")
            print(content)  # 🔥 Solo imprime el resumen
        else:
            print("⚠️ Error: No se encontró un resumen válido.")
    else:
        print("⚠️ Error: La API devolvió un JSON inesperado.")

except Exception as e:
    print(f"❌ Error: {e}")