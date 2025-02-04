import json
from llamaapi import LlamaAPI
import sys
import mylib


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

# Initialize the LlamaAPI with your API token
api_token = "LL-Z8mrEuQPmlMauJWuXwIDlnoi9bFiSlFqiYQSx8E3lEfEleU7Zt5YB3qGUgeKOf2e"
llama = LlamaAPI(api_token)

api_request_json = {
  "model": "llama3-70b",
  "messages": [
    {"role": "system", "content": "Resume este texto:\n"},
    {"role": "user", "content": texto},
  ]
}

# Make your request and handle the response
try:
    response = llama.run(api_request_json)
    if response.status_code == 200 and response.headers['Content-Type'] == 'application/json':
        content = response.json()['choices'][0]['message']['content']
        last_dot = content.rfind('.')
        last_newline = content.rfind('\n')
        cut_position = max(last_dot, last_newline)
        content = content[:cut_position+1]

        # Imprime el contenido recortado
        print(json.dumps(content, ensure_ascii=False))
    else:
        print(f"Error: HTTP {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except KeyError as e:
    print(f"Unexpected JSON structure: {e}")