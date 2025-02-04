import os
import shutil
import fitz
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, f1_score, cohen_kappa_score, matthews_corrcoef

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
    rutas = []
    for carpeta in directorios_interes:
        ruta_carpeta = os.path.join(directorio, carpeta)
        for archivo in os.listdir(ruta_carpeta):
            if archivo.endswith(".pdf"):
                ruta_archivo = os.path.join(ruta_carpeta, archivo)
                texto_archivo = extraer_texto(ruta_archivo)
                textos.append(texto_archivo)
                etiquetas.append(carpeta)
                rutas.append(ruta_archivo)
    return textos, etiquetas, rutas


# Configuración inicial
nltk.download('stopwords')
stop_words_spanish = stopwords.words('spanish')
vectorizador = TfidfVectorizer(stop_words=stop_words_spanish, max_features=1000)

# Cargar datos
directorios_interes = None
archivos_para_prueba = mover_archivos_para_pruebas("/Users/administrador/Desktop/PDFs", n=4, directorios_interes=directorios_interes)
textos, etiquetas, rutas_documentos = cargar_datos("/Users/administrador/Desktop/PDFs", directorios_interes)

# Transformar datos
X = vectorizador.fit_transform(textos)
y = etiquetas

# Entrenar Isolation Forest para detectar documentos atípicos
iso_forest = IsolationForest(n_estimators=100, contamination=0.05)  # 'auto' intenta estimar la contaminación
iso_forest.fit(X)

# Detectar si algún documento en el conjunto completo es una anomalía
anomalias = iso_forest.predict(X)

# Mostrar los documentos que son considerados anomalías
print("Documentos considerados anomalías:")
for i, is_anomaly in enumerate(anomalias):
    if is_anomaly == -1:
        print(f"Documento {rutas_documentos[i]} es una anomalía.")

# Dividir los datos en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entrenar el modelo de clasificación
modelo = MultinomialNB()
modelo.fit(X_train, y_train)

# Predicción y evaluación
y_pred = modelo.predict(X_test)

# Restaurar archivos
restaurar_archivos('/Users/administrador/Desktop/PDFs')

# Estadísticas generales del modelo
print("Estadísticas generales del modelo:")
print(classification_report(y_test, y_pred))
cm = confusion_matrix(y_test, y_pred, labels=["ACTAS", "CARTAS", "CUESTIONARIO"])
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=["ACTAS", "CARTAS", "CUESTIONARIO"], yticklabels=["ACTAS", "CARTAS", "CUESTIONARIO"])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()

print (cm)

print("Lo nuevo para el tfg:")
# Calcula la precisión (Accuracy)
accuracy = accuracy_score(y_test, y_pred)
print("Precisión (Accuracy):", accuracy)

# Calcula el F1-Score (puedes ajustar el promedio según sea necesario: 'micro', 'macro', 'weighted')
f1 = f1_score(y_test, y_pred, average='macro')
print("F1-Score:", f1)

# Calcula el Coeficiente Kappa de Cohen
kappa = cohen_kappa_score(y_test, y_pred)
print("Kappa de Cohen:", kappa)

# Calcula el Coeficiente de Correlación de Matthews (MCC)
mcc = matthews_corrcoef(y_test, y_pred)
print("Coeficiente de Correlación de Matthews (MCC):", mcc)