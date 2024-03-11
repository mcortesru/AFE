import mylib
import requests

text = mylib.corregir_erratas_texto(mylib.extraer_texto_pdf('./circulares/005-01.pdf'))

API_URL = "https://api-inference.huggingface.co/models/google/mt5-base"
headers = {"Authorization": f"Bearer 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"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

output = query({
    "inputs": "Resume este texto: " + text,
})

print(output)




