import mylib
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

texto = mylib.corregir_erratas_texto(mylib.extraer_texto_pdf())

print(summarizer(texto[:600], max_length=200, min_length=100, do_sample=False))

