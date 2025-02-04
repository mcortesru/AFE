import os
import shutil
import fitz
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from pycaret.classification import *
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Definición de funciones
def extraer_texto(ruta):
    texto = ""
    with fitz.open(ruta) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def cargar_datos(directorio, directorios_interes=None):
    if directorios_interes is None:
        directorios_interes = [d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d)) and d != 'PRUEBAS']
    textos = []
    etiquetas = []
    for carpeta in directorios_interes:
        ruta_carpeta = os.path.join(directorio, carpeta)
        for archivo in os.listdir(ruta_carpeta):
            if archivo.endswith(".pdf"):
                ruta_archivo = os.path.join(ruta_carpeta, archivo)
                texto_archivo = extraer_texto(ruta_archivo)
                textos.append(texto_archivo)
                etiquetas.append(carpeta)
    return textos, etiquetas

def cargar_datos_pruebas(directorio):
    textos_pruebas = []
    etiquetas_pruebas = []
    directorios_interes = [d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d))]
    
    for carpeta in directorios_interes:
        ruta_carpeta = os.path.join(directorio, carpeta, 'PRUEBAS')
        if os.path.exists(ruta_carpeta):
            for archivo in os.listdir(ruta_carpeta):
                if archivo.endswith(".pdf"):
                    ruta_archivo = os.path.join(ruta_carpeta, archivo)
                    texto_archivo = extraer_texto(ruta_archivo)
                    textos_pruebas.append(texto_archivo)
                    etiquetas_pruebas.append(carpeta)
                    
    return textos_pruebas, etiquetas_pruebas

def reservar_pruebas(directorio, num_pruebas=1):
    directorios_interes = [d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d))]
    for carpeta in directorios_interes:
        ruta_carpeta = os.path.join(directorio, carpeta)
        archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith('.pdf')]
        carpeta_pruebas = os.path.join(ruta_carpeta, 'PRUEBAS')
        if not os.path.exists(carpeta_pruebas):
            os.makedirs(carpeta_pruebas)
        for archivo in archivos[:num_pruebas]:
            shutil.move(os.path.join(ruta_carpeta, archivo), carpeta_pruebas)

# Configuración inicial
nltk.download('stopwords')
stop_words_spanish = stopwords.words('spanish')
vectorizador = TfidfVectorizer(stop_words=stop_words_spanish, max_features=1000)

# Reservar archivos para pruebas
reservar_pruebas("/Users/administrador/Desktop/PDFs", num_pruebas=20)

# Cargar y procesar datos
textos, etiquetas = cargar_datos("/Users/administrador/Desktop/PDFs")
X = vectorizador.fit_transform(textos)
y = etiquetas

# Crear DataFrame para PyCaret
df_features = pd.DataFrame(X.toarray(), columns=vectorizador.get_feature_names_out())
df_labels = pd.DataFrame(y, columns=['label'])
df = pd.concat([df_features, df_labels], axis=1)

# Configuración de PyCaret
clf1 = setup(data=df, target='label', session_id=123, html=False)

# Comparar modelos para encontrar el mejor
best_model = compare_models()

# Evaluación detallada del modelo elegido
evaluate_model(best_model)

# Finalizar el modelo
final_model = finalize_model(best_model)

# Guardar el modelo
import joblib
save_model(final_model, 'final_model')
joblib.dump(vectorizador, '/Users/administrador/AFE/vectorizador.pkl')

# Cargar los ficheros de prueba
textos_pruebas, etiquetas_pruebas = cargar_datos_pruebas("/Users/administrador/Desktop/PDFs")

# Transformar los datos de prueba con el vectorizador existente
X_pruebas = vectorizador.transform(textos_pruebas)

# Crear DataFrame para los datos de prueba
df_pruebas = pd.DataFrame(X_pruebas.toarray(), columns=vectorizador.get_feature_names_out())

# Predicción con el modelo finalizado
predicciones_pruebas = predict_model(final_model, data=df_pruebas)

# Inspeccionar las columnas del DataFrame de predicciones
print(predicciones_pruebas.head())  # Inspecciona las columnas disponibles

# Comparación de las predicciones con las etiquetas reales
predicciones_pruebas['Real'] = etiquetas_pruebas

# Mostrar los resultados de las predicciones junto a las etiquetas reales
print(predicciones_pruebas[['prediction_label', 'Real']])

# Calcular y mostrar las métricas de clasificación
print("\nConfusion Matrix:")
print(confusion_matrix(predicciones_pruebas['Real'], predicciones_pruebas['prediction_label']))

print("\nClassification Report:")
print(classification_report(predicciones_pruebas['Real'], predicciones_pruebas['prediction_label']))

print("\nAccuracy Score:")
print(accuracy_score(predicciones_pruebas['Real'], predicciones_pruebas['prediction_label']))
