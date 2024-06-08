import mylib
import sys
from flair.data import Sentence
from flair.models import SequenceTagger
from span_marker import SpanMarkerModel
import requests
from flair.models import SequenceTagger
from flair.data import Sentence
from prettytable import PrettyTable

# /Users/administrador/Desktop/PDFs/ACTAS/004-07-147.pdf

if len(sys.argv) < 2:
    # path_al_archivo = input("No se ha proporcionado el path del archivo. Por favor, introduce el path del archivo: ")   
     path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-147.pdf" 
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-68-69.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-71.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/005-11-30-33.pdf"  # MUY LARGO
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-165-168.pdf"
else:
    path_al_archivo = sys.argv[1]

try:
    texto_original = mylib.extraer_texto_pdf(path_al_archivo)
    texto_corregido = mylib.quitar_guion_y_espacio(texto_original)

    # Paso 1: Recolectar datos de los tres modelos

    # Span Marker Model (BERT)
    from transformers import AutoTokenizer
    from span_marker import SpanMarkerModel

    # Cargar el tokenizador y el modelo
    tokenizer = AutoTokenizer.from_pretrained("alvarobartt/bert-base-multilingual-cased-ner-spanish")
    model = SpanMarkerModel.from_pretrained("alvarobartt/bert-base-multilingual-cased-ner-spanish")

    def segmentar_texto(texto, max_length=400):
        # Tokenizar el texto
        tokens = tokenizer.tokenize(texto)
        segmentos = []
        current_segment = []
        current_length = 0

        for token in tokens:
            if token.startswith("##"):
                # Agregar el token al segmento actual si es una continuación de una palabra
                current_segment.append(token)
                current_length += 1
            else:
                # Comenzar un nuevo segmento si es necesario
                if current_length >= max_length:
                    segmento = tokenizer.convert_tokens_to_string(current_segment)
                    segmentos.append(segmento)
                    current_segment = []
                    current_length = 0
                current_segment.append(token)
                current_length += 1

        # Agregar el último segmento si contiene texto
        if current_segment:
            segmento = tokenizer.convert_tokens_to_string(current_segment)
            segmentos.append(segmento)

        return segmentos
    
    # Segmentar el texto
    segmentos = segmentar_texto(texto_corregido)

    # Procesar cada segmento con el modelo
    for segmento in segmentos:
        entities_bert = model.predict(segmento)


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
    output = response.json()

    print("\n\n")
    # Paso 2: Consolidar las entidades en un diccionario común
    # Consolidar las entidades en un diccionario común
    all_entities = {}
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

    print("Tabla completa de entidades antes de filtrar:")
    print(table_all)

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

    print("\nTabla filtrada de entidades que cumplen los criterios específicos:")
    print(table_filtered)
    print("\n")

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
    print("FECHAS ENCONTRADAS:")
    for item in fechas_con_contexto:
        # print(f"\n\nFecha: {item['fecha']} \n\tTexto: {item['texto_fecha']} \n\tContexto: {item['contexto']} \n\tInicio - Fin: {item['start_context']} - {item['end_context']}")
        print(f"\n\nFecha: {item['fecha']}")

except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)
