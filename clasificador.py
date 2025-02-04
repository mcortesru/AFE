import os
import sys
import fitz
import nltk
import joblib
import pandas as pd
from nltk.corpus import stopwords
from pycaret.classification import load_model, predict_model

# Asegurarse de que los stopwords de NLTK estén descargados
nltk.download('stopwords')
stop_words_spanish = stopwords.words('spanish')

# Cargar el modelo y el vectorizador guardado
modelo_path = '/Users/administrador/AFE/final_model'
vectorizador_path = '/Users/administrador/AFE/vectorizador.pkl'
modelo = load_model(modelo_path)
vectorizador = joblib.load(vectorizador_path)

# Función para extraer texto de un archivo PDF
def extraer_texto(ruta):
    texto = ""
    with fitz.open(ruta) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

# Procesar el archivo PDF proporcionado
def procesar_archivo(ruta_archivo):
    texto = extraer_texto(ruta_archivo)
    X = vectorizador.transform([texto])
    df = pd.DataFrame(X.toarray(), columns=vectorizador.get_feature_names_out())
    predicciones = predict_model(modelo, data=df)
    return predicciones['prediction_label'].iloc[0]

if __name__ == "__main__":
    ruta_archivo = sys.argv[1]
    tipo_documento = procesar_archivo(ruta_archivo)
    print(f"El tipo de documento es: {tipo_documento}")
    
    output_dir = '/tmp'
    output_file = 'clasificacion.txt'
    
    # Asegurar que el directorio exista
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Escribir la salida en el archivo
    with open(os.path.join(output_dir, output_file), 'w') as file:
        file.write("El tipo de documento es: " + tipo_documento)
