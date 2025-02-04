import json
from llamaapi import LlamaAPI
import sys
import mylib
import requests

def find_last_number(content):
    last_index = -1
    # Recorre la cadena en reversa
    for i in range(len(content) - 1, -1, -1):
        if content[i].isdigit():
            last_index = i
        elif last_index != -1:
            # Retorna el índice justo después del último dígito numérico encontrado
            return last_index
    return last_index


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

else:
    path_al_archivo = sys.argv[1]

try:
    texto = mylib.extraer_texto_pdf(path_al_archivo)
except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)

# 📌 Inicializar LlamaAPI con tu API Key
api_token = "LL-Z8mrEuQPmlMauJWuXwIDlnoi9bFiSlFqiYQSx8E3lEfEleU7Zt5YB3qGUgeKOf2e"
llama = LlamaAPI(api_token)

# 📌 Construcción de la solicitud
api_request_json = {
    "model": "llama3.1-70b",  # 🔹 Usa un modelo válido
    "messages": [
        {"role": "system", "content": "Extrae las palabras clave de este texto:"},
        {"role": "user", "content": texto},
    ],
    "stream": False
}


# 📌 Hacer la solicitud y manejar la respuesta
try:
    response = llama.run(api_request_json)
    response_json = response.json()

    # 📌 Verificar si la respuesta es válida
    if isinstance(response_json, dict) and "choices" in response_json:
        choices = response_json["choices"]
        if isinstance(choices, list) and len(choices) > 0 and "message" in choices[0]:
            content = choices[0]["message"].get("content", "")
            print(content)  # 🔥 Solo imprime las palabras clave
    else:
        sys.exit("⚠️ Error: No se encontraron palabras clave.")

except Exception:
    sys.exit("⚠️ Error al procesar la solicitud.")