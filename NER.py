import sys
from flair.data import Sentence
from flair.models import SequenceTagger
from span_marker import SpanMarkerModel
import requests
from flair.models import SequenceTagger
from flair.data import Sentence
from prettytable import PrettyTable
import os

import time
import fitz
import re

def extraer_texto_pdf(ruta_pdf):
    doc = fitz.open(ruta_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

def quitar_guion_y_espacio(texto):
    texto_limpiado = re.sub(r'(\b-\s*|\s*-\s*)([^\W\d_])', r'\2', texto)
    return texto_limpiado


start_time = time.time()  # Registrar el tiempo de inicio

if len(sys.argv) < 2:
    # path_al_archivo = input("No se ha proporcionado el path del archivo. Por favor, introduce el path del archivo: ")   
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-147.pdf" 
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-68-69.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-71.pdf"
     path_al_archivo = "/Users/administrador/Desktop/PDFs/Documentos/ACTAS/005-11-30-33.pdf"  # MUY LARGO
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-165-168.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-155.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-154.pdf"

else:
    path_al_archivo = sys.argv[1]

try:
    texto_original = extraer_texto_pdf(path_al_archivo)
    texto_corregido = quitar_guion_y_espacio(texto_original)
    all_entities = {}


    # Paso 1: Recolectar datos de los tres modelos
    # Span Marker Model (BERT)
    print("procesando con BERT")
    from transformers import AutoTokenizer
    from span_marker import SpanMarkerModel

    # Cargar el tokenizador y el modelo
    tokenizer = AutoTokenizer.from_pretrained("alvarobartt/bert-base-multilingual-cased-ner-spanish")
    model = SpanMarkerModel.from_pretrained("alvarobartt/bert-base-multilingual-cased-ner-spanish")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    def segmentar_texto(texto, max_length=512):
        # Tokenizar el texto de entrada en subpalabras
        tokenized = tokenizer.encode_plus(texto, add_special_tokens=True, truncation=True, return_tensors="pt")
        input_ids = tokenized["input_ids"][0].tolist()  # Convertir a lista de enteros

        # Dividir el texto en fragmentos de tamaño máximo permitido
        segmentos = []
        start = 0
        while start < len(input_ids):
            end = min(start + max_length - 2, len(input_ids))  # Restar 2 para espacio de [CLS] y [SEP]
            segment = input_ids[start:end]
            
            # Convertir de nuevo a texto
            segment_text = tokenizer.decode(segment, skip_special_tokens=True)
            segmentos.append(segment_text)
            start = end  # Mover al siguiente fragmento

        return segmentos
    
    # Segmentar el texto correctamente
    segmentos = segmentar_texto(texto_corregido)
    print(f"Texto segmentado en {len(segmentos)} partes.")

    # Procesar cada segmento con el modelo
    entities_bert = []
    for i, segmento in enumerate(segmentos):
        print(f"Procesando segmento {i+1}/{len(segmentos)}...")

        try:
            entidades = model.predict(segmento)
            entities_bert.extend(entidades)
        except Exception as e:
            print(f"❌ Error en segmento {i+1}: {e}")

    print("Entidades detectadas:", entities_bert)


    # Flair
    print("Procesando con Flair...")
    tagger_flair = SequenceTagger.load("flair/ner-spanish-large")
    sentence_flair = Sentence(texto_corregido)
    tagger_flair.predict(sentence_flair)
    entities_flair = [(entity.text, entity.tag, entity.score) for entity in sentence_flair.get_spans('ner')]
    
    # XLM-Roberta
    print("Procesando con XLM-Roberta...")
    API_URL = "https://api-inference.huggingface.co/models/MMG/xlm-roberta-large-ner-spanish"
    headers = {"Authorization": "Bearer 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"}
    response = requests.post(API_URL, headers=headers, json={"inputs": texto_corregido})

    try:
        output = response.json()
        # Verificar que output es una lista de diccionarios con las claves esperadas
        if isinstance(output, list) and all(isinstance(item, dict) for item in output):
            for entity in output:
                if entity.get('score', 0) > 0.8 and 'word' in entity and 'entity_group' in entity:
                    all_entities.setdefault(entity['word'], {}).update({"Roberta": (entity['entity_group'], entity['score'])})
        else:
            print("Formato inesperado en la respuesta de la API")
            output = []
    except Exception as e:
        print(f"Error procesando la respuesta: {e}")
        print(response.text)
        output = []

    print("\n\n")
    # Paso 2: Consolidar las entidades en un diccionario común

    for entity in entities_flair:
        all_entities.setdefault(entity[0], {}).update({"Flair": (entity[1], entity[2])})
    for entity in entities_bert:
        all_entities.setdefault(entity['span'], {}).update({"BERT": (entity['label'], entity['score'])})
    for entity in output:
        if entity['score'] > 0.8:
            all_entities.setdefault(entity['word'], {}).update({"Roberta": (entity['entity_group'], entity['score'])})

    tipo_prioridad = {'PER': 1, 'LOC': 2, 'ORG': 3, 'MISC': 4}
    # Crear una tabla para todas las entidades
    table_all = PrettyTable()
    table_all.field_names = ["Entidad", "Tipo Flair", "Confianza Flair", "Tipo BERT", "Confianza BERT", "Tipo Roberta", "Confianza Roberta"]
    rows_all = []
    for entity, details in all_entities.items():
        row = [entity]
        for model in ["Flair", "BERT", "Roberta"]:
            info = details.get(model, ("-", "-"))
            row.extend([info[0], f"{info[1]:.2f}" if isinstance(info[1], (float, int)) else "-"])
        rows_all.append(row)

    # Ordenar las filas por tipo de entidad usando la prioridad definida
    rows_all.sort(key=lambda x: (tipo_prioridad.get(x[1], 5), tipo_prioridad.get(x[3], 5), tipo_prioridad.get(x[5], 5)))
    for row in rows_all:
        table_all.add_row(row)

    # print("Tabla completa de entidades antes de filtrar:")
    # print(table_all)

    # Crear una tabla filtrada de entidades
    table_filtered = PrettyTable()
    table_filtered.field_names = ["Entidad", "Tipo Flair", "Confianza Flair", "Tipo BERT", "Confianza BERT", "Tipo Roberta", "Confianza Roberta"]
    rows_filtered = []
    for entity, details in all_entities.items():
        count_models = sum(1 for model in details if model in ["Flair", "BERT", "Roberta"] and details[model] != ("-","-"))
        is_high_confidence = any(details[model][1] > 0.99 for model in details if model in ["Flair", "BERT"])
        if count_models > 1 or (count_models == 1 and is_high_confidence):
            row = [entity]
            for model in ["Flair", "BERT", "Roberta"]:
                info = details.get(model, ("-", "-"))
                # Asegurarse que el valor de confianza se muestra correctamente
                if isinstance(info[1], (float, int)):
                    confianza = f"{info[1]:.2f}"
                elif isinstance(info[1], str) and info[1].replace('.', '', 1).isdigit():
                    confianza = f"{float(info[1]):.2f}"
                else:
                    confianza = "-"
                row.extend([info[0], confianza])
            rows_filtered.append(row)

    # Ordenar las filas por tipo de entidad para la tabla filtrada
    rows_filtered.sort(key=lambda x: (tipo_prioridad.get(x[1], 5), tipo_prioridad.get(x[3], 5), tipo_prioridad.get(x[5], 5)))
    for row in rows_filtered:
        table_filtered.add_row(row)

    # print("\nTabla filtrada de entidades que cumplen los criterios específicos:")
    print(table_filtered)
    print("\n")
    html_table = table_filtered.get_html_string()
    # print (html_table)

    # BUSCADOR DE FECHAS QUE NO FUNCIONA TAN BIEN
    # from dateutil.parser import parse
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
    resultados = search_dates(texto_corregido, languages=['es'])

    fechas_con_contexto = []
    fechas_vistas = set()  # Un conjunto para almacenar fechas ya vistas

    if resultados:
        for texto_fecha, fecha_obj in resultados:
            año = fecha_obj.year
            # Ajustar el año si es mayor a 2030, restando 100
            if año > 2030:
                fecha_obj = fecha_obj.replace(year=año - 100)
                fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
            # Ignorar el año si está entre 2000 y 2030
            elif 2000 <= año <= 2030:
                fecha_formateada = fecha_obj.strftime("%m-%d")
            # Si el año es menor de 2000, se mantiene el formato completo
            else:
                fecha_formateada = fecha_obj.strftime("%Y-%m-%d")

            inicio = texto_corregido.find(texto_fecha)
            start_context = max(inicio - 30, 0)
            end_context = inicio + len(texto_fecha) + 30
            contexto = texto_corregido[start_context:end_context].strip()

            if fecha_formateada not in fechas_vistas:
                fechas_vistas.add(fecha_formateada)
                fechas_con_contexto.append({
                    'fecha': fecha_formateada,
                    'contexto': contexto,
                    'texto_fecha': texto_fecha,
                    'start_context': start_context,
                    'end_context': end_context
                })

    # Mostrar las fechas interpretadas y sus contextos
    # print("FECHAS ENCONTRADAS:")
    # for item in fechas_con_contexto:
    #     # print(f"\n\nFecha: {item['fecha']} \n\tTexto: {item['texto_fecha']} \n\tContexto: {item['contexto']} \n\tInicio - Fin: {item['start_context']} - {item['end_context']}")
    #     print(f"\n\nFecha: {item['fecha']}")
    print (html_table)
    output_dir = os.path.join(os.path.dirname(__file__), '.tmp')
    output_file = os.path.join(output_dir, 'NERS.txt')
    
    # Asegurar que el directorio exista
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Escribir la tabla HTML en el archivo
    with open(os.path.join(output_dir, output_file), 'w') as file:
        file.write(html_table)



except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)


# end_time = time.time()
# execution_time = end_time - start_time

# print(f"El tiempo de ejecución fue: {execution_time} segundos")
