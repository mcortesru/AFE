import os
import fitz
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report

def extraer_texto(ruta):
    texto = ""
    with fitz.open(ruta) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def cargar_datos(directorio):
    textos = []
    etiquetas = []
    archivos = []
    for carpeta in os.listdir(directorio):
        ruta_carpeta = os.path.join(directorio, carpeta)
        if os.path.isdir(ruta_carpeta):
            for archivo in os.listdir(ruta_carpeta):
                if archivo.endswith(".pdf"):
                    ruta_archivo = os.path.join(ruta_carpeta, archivo)
                    texto_archivo = extraer_texto(ruta_archivo)
                    textos.append(texto_archivo)
                    etiquetas.append(carpeta)
                    archivos.append(ruta_archivo)
    return textos, etiquetas, archivos

# Configuración inicial
nltk.download('stopwords')
stop_words_spanish = stopwords.words('spanish')
vectorizador = TfidfVectorizer(stop_words=stop_words_spanish, max_features=1000)

# Cargar datos
directorios_base = "/Users/administrador/Desktop/PDFs"
textos, etiquetas, archivos = cargar_datos(directorios_base)

# Transformar datos y entrenar modelo
X = vectorizador.fit_transform(textos)
y = etiquetas
X_train, X_test, y_train, y_test, archivos_train, archivos_test = train_test_split(X, y, archivos, test_size=0.2, random_state=42)
modelo = MultinomialNB()
modelo.fit(X_train, y_train)

# Predicción y evaluación
y_pred = modelo.predict(X_test)
print(classification_report(y_test, y_pred))

# Evaluar todos los archivos y registrar los detalles de predicción
umbral_confianza = 0.6
archivos_baja_confianza = []

for i, archivo in enumerate(archivos_test):
    pred_prob = modelo.predict_proba(X_test[i])[0]
    confianza = max(pred_prob)
    pred_label = modelo.classes_[pred_prob.argmax()]
    etiqueta_real = y_test[i]
    correcto = pred_label == etiqueta_real
    if confianza < umbral_confianza:
        archivos_baja_confianza.append((archivo, etiqueta_real, pred_label, confianza, correcto))

# Imprimir archivos con baja confianza
print("Archivos con baja confianza en su clasificación:")
for archivo, real, pred, conf, correcto in archivos_baja_confianza:
    estado = "Correcta" if correcto else "Incorrecta"
    print(f"Archivo: {archivo}\nEtiqueta Real: {real}\nEtiqueta Predicha: {pred}\nConfianza: {conf:.4f}\nClasificación: {estado}\n")
