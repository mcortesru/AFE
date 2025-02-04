import os
import fitz
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from pycaret.classification import *
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
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

# Cargar y procesar datos
textos, etiquetas = cargar_datos("/Users/administrador/Desktop/PDFs")
X = vectorizador.fit_transform(textos)
y = etiquetas

# ------------------- Enfoque con PyCaret -------------------

# Crear DataFrame para PyCaret
df_features = pd.DataFrame(X.toarray(), columns=vectorizador.get_feature_names_out())
df_labels = pd.DataFrame(y, columns=['label'])
df = pd.concat([df_features, df_labels], axis=1)

# Configuración de PyCaret con división de datos
clf1 = setup(data=df, target='label', session_id=123, html=False, train_size=0.8)

# Comparar modelos para encontrar el mejor
best_model = compare_models()

# Evaluación detallada del modelo elegido
evaluate_model(best_model)

# Finalizar el modelo
final_model = finalize_model(best_model)

# Predicción en el conjunto de prueba
predicciones_pruebas = predict_model(final_model)

# Comparación de las predicciones con las etiquetas reales
print("\nResultados del modelo entrenado con PyCaret:")
print(predicciones_pruebas[['label', 'prediction_label']])

# Calcular y mostrar las métricas de clasificación
print("\nConfusion Matrix:")
print(confusion_matrix(predicciones_pruebas['label'], predicciones_pruebas['prediction_label']))

print("\nClassification Report:")
print(classification_report(predicciones_pruebas['label'], predicciones_pruebas['prediction_label']))

print("\nAccuracy Score:")
print(accuracy_score(predicciones_pruebas['label'], predicciones_pruebas['prediction_label']))

# ------------------- Enfoque con Scikit-Learn -------------------

# Separar los datos en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entrenar el modelo
modelo = MultinomialNB()
modelo.fit(X_train, y_train)

# Predicción y evaluación
y_pred = modelo.predict(X_test)

# Mostrar las estadísticas generales del modelo
print("\nEstadísticas generales del modelo entrenado con Scikit-Learn:")
print(classification_report(y_test, y_pred))
print("\nAccuracy Score:")
print(accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
