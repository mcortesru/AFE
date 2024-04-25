import os
import shutil
import fitz
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
import random

def extraer_texto(ruta):
    texto = ""
    with fitz.open(ruta) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def mover_archivos_para_pruebas(directorio, subdirectorio='PRUEBAS', n=3, directorios_interes=None):
    if directorios_interes is None:
        directorios_interes = os.listdir(directorio)
    archivos_movidos = {}
    for carpeta in directorios_interes:
        ruta_carpeta = os.path.join(directorio, carpeta)
        if os.path.isdir(ruta_carpeta):
            archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith('.pdf')]
            random.shuffle(archivos)
            ruta_subdirectorio = os.path.join(ruta_carpeta, subdirectorio)
            if not os.path.exists(ruta_subdirectorio):
                os.makedirs(ruta_subdirectorio)
            for archivo in archivos[:n]:
                src_path = os.path.join(ruta_carpeta, archivo)
                dest_path = os.path.join(ruta_subdirectorio, archivo)
                shutil.move(src_path, dest_path)
                archivos_movidos[dest_path] = src_path
    return archivos_movidos

def restaurar_archivos(directorio):
    for carpeta in os.listdir(directorio):
        ruta_carpeta = os.path.join(directorio, carpeta)
        subdirectorio_pruebas = os.path.join(ruta_carpeta, 'PRUEBAS')
        if os.path.isdir(subdirectorio_pruebas):
            for archivo in os.listdir(subdirectorio_pruebas):
                ruta_completa_archivo = os.path.join(subdirectorio_pruebas, archivo)
                destino_archivo = os.path.join(ruta_carpeta, archivo)
                try:
                    shutil.move(ruta_completa_archivo, destino_archivo)
                    #print(f"Archivo {archivo} movido de {ruta_completa_archivo} a {destino_archivo}")
                except Exception as e:
                    print(f"No se pudo mover el archivo {archivo} de {ruta_completa_archivo} a {destino_archivo}: {e}")

def cargar_datos(directorio, directorios_interes=None):
    if directorios_interes is None:
        directorios_interes = [d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d))]
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


# Configuración inicial
nltk.download('stopwords')
stop_words_spanish = stopwords.words('spanish')
vectorizador = TfidfVectorizer(stop_words=stop_words_spanish, max_features=1000)

# Cargar datos
directorios_interes = None
#archivos_para_prueba = mover_archivos_para_pruebas("/Users/administrador/Desktop/PDFs", n=2, directorios_interes=directorios_interes)
textos, etiquetas = cargar_datos("/Users/administrador/Desktop/PDFs", directorios_interes)

# Transformar datos y entrenar modelo
X = vectorizador.fit_transform(textos)
y = etiquetas
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
modelo = MultinomialNB()
modelo.fit(X_train, y_train)

# Predicción y evaluación
y_pred = modelo.predict(X_test)

# Evaluación detallada de cada archivo de prueba
'''for archivo in archivos_para_prueba:
    texto = extraer_texto(archivo)
    X_prueba = vectorizador.transform([texto])
    pred_prob = modelo.predict_proba(X_prueba)[0]
    pred_label = modelo.predict(X_prueba)[0]
    real_label = archivo.split('/')[-3]  # Asumiendo que la estructura de carpetas contiene la etiqueta
    correcto = "Sí" if pred_label == real_label else "No"
    print(f"Archivo: {archivo}")
    print(f"Etiqueta real: {real_label}")
    print(f"Etiqueta predicha: {pred_label}")
    print(f"Predicción correcta: {correcto}")
    print("Probabilidades de clase:")
    for label, prob in zip(modelo.classes_, pred_prob):
        print(f"{label}: {prob:.4f}")
    print("\n")'''

# Restaurar archivos
restaurar_archivos('/Users/administrador/Desktop/PDFs')

# Estadísticas generales del modelo
print("Estadísticas generales del modelo:")
print(classification_report(y_test, y_pred))

'''
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Convertir listas a Series de pandas
y_train_series = pd.Series(y_train)
y_test_series = pd.Series(y_test)

# Contar ocurrencias de cada clase
train_counts = y_train_series.value_counts()
test_counts = y_test_series.value_counts()

# Crear gráficos para visualizar las distribuciones
fig, axes = plt.subplots(1, 2, figsize=(14, 7), sharey=True)
sns.barplot(x=train_counts.index, y=train_counts.values, ax=axes[0])
axes[0].set_title('Distribución de Clases en el Conjunto de Entrenamiento')
axes[0].set_xlabel('Clase')
axes[0].set_ylabel('Cantidad')

sns.barplot(x=test_counts.index, y=test_counts.values, ax=axes[1])
axes[1].set_title('Distribución de Clases en el Conjunto de Prueba')
axes[1].set_xlabel('Clase')

plt.xticks(rotation=90)
plt.show()
'''
