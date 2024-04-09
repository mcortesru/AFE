from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import numpy as np
import mylib

# Cargar las palabras de parada en español de NLTK
spanish_stopwords = stopwords.words('spanish')

def extraer_palabras_clave_tfidf(texto, top_n=10):
    # Inicializar el vectorizador TF-IDF con las palabras de parada de NLTK
    vectorizador = TfidfVectorizer(stop_words=spanish_stopwords)
    
    # Ajustar y transformar el texto
    tfidf_matrix = vectorizador.fit_transform([texto])
    
    # Obtener las características (palabras)
    palabras = np.array(vectorizador.get_feature_names_out())
    
    # Sumar los valores TF-IDF para cada palabra y obtener los índices ordenados
    suma_tfidf = tfidf_matrix.sum(axis=0)
    indices_ordenados = np.argsort(suma_tfidf).flatten()[::-1]
    
    # Extraer las top n palabras clave
    palabras_clave = palabras[indices_ordenados][:top_n]
    
    return palabras_clave

# Asegúrate de reemplazar "Tu texto extraído del PDF aquí" con el texto real extraído de tu PDF
texto_pdf = mylib.extraer_texto_pdf()
palabras_clave = extraer_palabras_clave_tfidf(texto_pdf)
print("Palabras clave:", palabras_clave)
