import mylib
import sys
from flair.data import Sentence
from flair.models import SequenceTagger
from span_marker import SpanMarkerModel
import requests
import spacy

# /Users/administrador/Desktop/PDFs/ACTAS/004-07-147.pdf

if len(sys.argv) < 2:
    # path_al_archivo = input("No se ha proporcionado el path del archivo. Por favor, introduce el path del archivo: ")   
    path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-147.pdf" 
else:
    path_al_archivo = sys.argv[1]

try:
    texto_original = mylib.extraer_texto_pdf(path_al_archivo)
    texto_corregido = mylib.quitar_guion_y_espacio(texto_original)
    # print(texto_corregido)
    print(texto_corregido)

    # Método 1: Flair NER Spanish Large
    tagger_flair = SequenceTagger.load("flair/ner-spanish-large")
    sentence_flair = Sentence(texto_corregido)
    tagger_flair.predict(sentence_flair)
    entities_flair = [(entity.text, entity.tag, entity.score) for entity in sentence_flair.get_spans('ner')]
    print("Entidades NER encontradas con Flair NER Spanish Large:")
    print(entities_flair)
    print()
    print()

    # Método 2: Span Marker Model (Bert-based)
    model_bert = SpanMarkerModel.from_pretrained("alvarobartt/bert-base-multilingual-cased-ner-spanish")
    entities_bert = model_bert.predict(texto_corregido)
    print("Entidades NER encontradas con Span Marker Model (Bert-based):")
    print(entities_bert)
    print()
    print()
    
    # Método 3: MMG XLM-Roberta Large NER Spanish
    API_URL = "https://api-inference.huggingface.co/models/MMG/xlm-roberta-large-ner-spanish"
    headers = {"Authorization": "Bearer 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"}

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
        
    output = query({
        "inputs": texto_corregido
    })

    filtered_data = []
    for entity in output:
        entity_info = {
            'entity': entity['entity_group'],
            'word': entity['word'],
            'score': entity['score'],
            'start': entity['start'], 
            'end': entity['end']
        }
        filtered_data.append(entity_info)

    # Imprimir los resultados filtrados
    print("Entidades NER encontradas con MMG XLM-Roberta Large NER Spanish:")
    for data in filtered_data:
        if data['score'] > 0.8:  # Use data['score'] instead of data.score
            print(data)
    print()
    print()



    # BUSCADOR DE FECHAS QUE NO FUNCIONA TAN BIEN
    # from dateutil.parser import parse
    # print(texto_corregido)
    # def buscar_fechas(texto):
    #     palabras = texto.split()
    #     fechas = []
    #     for palabra in palabras:
    #         try:
    #             posible_fecha = parse(palabra, fuzzy=False)
    #             fechas.append(posible_fecha)
    #         except ValueError:
    #             continue
    #     return fechas

    # fechas_encontradas = buscar_fechas(texto_corregido)
    # print(fechas_encontradas)
    # print()


    from dateparser.search import search_dates
    import re

    resultados = search_dates(texto_corregido, languages=['es'])

    fechas_con_contexto = []
    fechas_vistas = set()  # Un conjunto para almacenar fechas ya vistas

    if resultados:
        for texto_fecha, fecha_obj in resultados:
            fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
            año = fecha_obj.year
            if año <= 2000:
                inicio = texto_corregido.find(texto_fecha)
                start_context = max(inicio - 30, 0)
                end_context = inicio + len(texto_fecha) + 30
                contexto = texto_corregido[start_context:end_context].strip()

                if fecha_formateada not in fechas_vistas:
                    fechas_vistas.add(fecha_formateada)
                    fechas_con_contexto.append({
                        'fecha': fecha_formateada,
                        'contexto': contexto,
                        'texto_fecha': texto_fecha
                    })

    # Mostrar las fechas interpretadas y sus contextos
    print("FECHAS ENCONTRADAS:")
    for item in fechas_con_contexto:
        print(f"Fecha: {item['fecha']}")


except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)
