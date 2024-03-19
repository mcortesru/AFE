import mylib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

def preparar_dataset(directorio_base):
    documentos = []
    etiquetas = []
    # Directorios específicos para circulares y otros documentos
    directorio_circulares = os.path.join(directorio_base, 'CircularesDivididas')
    directorio_otros = os.path.join(directorio_base, 'OtrosDocumentos')
    
    # Procesa circulares
    for raiz, dirs, archivos in os.walk(directorio_circulares):
        for archivo in archivos:
            if archivo.endswith('.pdf'):
                ruta_completa = os.path.join(raiz, archivo)
                texto = mylib.extraer_texto_pdf(ruta_completa).strip()
                if texto:
                    documentos.append(texto)
                    etiquetas.append('circular')

    # Procesa otros documentos
    for raiz, dirs, archivos in os.walk(directorio_otros):
        for archivo in archivos:
            if archivo.endswith('.pdf'):
                ruta_completa = os.path.join(raiz, archivo)
                textos_por_pagina = mylib.extraer_texto_por_pagina(ruta_completa)
                for texto in textos_por_pagina:
                    texto = texto.strip()
                    if texto:
                        documentos.append(texto)
                        etiquetas.append('otro')

    return documentos, etiquetas

def preparar_datos_comprobacion(directorio_base):
    documentos_comprobacion = []
    nombres_archivos = []  # Lista para almacenar los nombres de los archivos
    for raiz, dirs, archivos in os.walk(directorio_base):
        for archivo in archivos:
            if archivo.endswith('.pdf'):
                ruta_completa = os.path.join(raiz, archivo)
                texto = mylib.extraer_texto_pdf(ruta_completa).strip()
                if texto:
                    documentos_comprobacion.append(texto)
                    nombres_archivos.append(archivo)  # Almacena el nombre del archivo
    return documentos_comprobacion, nombres_archivos  # Devuelve también los nombres de los archivos




documentos, etiquetas = preparar_dataset('/Users/administrador/AFE')

# Inicialización del vectorizador
vectorizador = TfidfVectorizer(stop_words=None, lowercase=True, token_pattern=r'\b\w+\b')

try:
    X = vectorizador.fit_transform(documentos)
    X_train, X_test, y_train, y_test = train_test_split(X, etiquetas, test_size=0.2, random_state=42, stratify=etiquetas)

    modelo = LogisticRegression(class_weight='balanced')
    modelo.fit(X_train, y_train)

    predicciones = modelo.predict(X_test)
    print(accuracy_score(y_test, predicciones))
    print(classification_report(y_test, predicciones))
except ValueError as e:
    print("Error al vectorizar los documentos:", e)


documentos_comprobacion, nombres_archivos = preparar_datos_comprobacion('./paraComprobar')

if documentos_comprobacion:
    X_comprobacion = vectorizador.transform(documentos_comprobacion)
    predicciones_comprobacion = modelo.predict(X_comprobacion)

    for i, pred in enumerate(predicciones_comprobacion):
        # Imprime tanto la predicción como el nombre del archivo asociado
        print(f"{nombres_archivos[i]}: Predicción - {pred}")
else:
    print("No se encontraron documentos válidos para comprobación.")

# Asumiendo que ya has preparado tu dataset y tienes la lista 'etiquetas'
num_circulares = etiquetas.count('circular')
num_otros = etiquetas.count('otro')

print(f"Total de documentos etiquetados como 'circular': {num_circulares}")
print(f"Total de documentos etiquetados como 'otro': {num_otros}")
