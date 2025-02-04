import mylib
import sys
from span_marker import SpanMarkerModel
import requests






if len(sys.argv) < 2:
     path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-154.pdf"

else:
    path_al_archivo = sys.argv[1]

try:
    texto_original = mylib.extraer_texto_pdf(path_al_archivo)
    texto_corregido = mylib.quitar_guion_y_espacio(texto_original)


    # XLM-Roberta
    print("Procesando con XLM-Roberta...")
    API_URL = "https://api-inference.huggingface.co/models/MMG/xlm-roberta-large-ner-spanish"
    headers = {"Authorization": "Bearer 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"}
    response = requests.post(API_URL, headers=headers, json={"inputs": texto_corregido})
    output = response.json()
    print(output)

except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)