import os
import sys
import fitz
import nltk
import joblib
import pandas as pd
from nltk.corpus import stopwords
from pycaret.classification import load_model, predict_model

# Definir la carpeta base del proyecto de manera dinámica
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Rutas del modelo y vectorizador de forma compatible con todos los sistemas
modelo_path = os.path.join(BASE_DIR, "final_model")
vectorizador_path = os.path.join(BASE_DIR, "vectorizador.pkl")

# Cargar el modelo y vectorizador guardados
modelo = load_model(modelo_path)
vectorizador = joblib.load(vectorizador_path)

# Asegurarse de que los stopwords de NLTK estén descargados
nltk.download('stopwords')
stop_words_spanish = stopwords.words('spanish')

# Extraer texto de un PDF
def extraer_texto_pdf(ruta_pdf):
    with fitz.open(ruta_pdf) as doc:
        return "\n".join([pagina.get_text() for pagina in doc])

# Procesar el archivo PDF proporcionado
def procesar_archivo(ruta_archivo):
    texto = extraer_texto_pdf(ruta_archivo)
    X = vectorizador.transform([texto])
    df = pd.DataFrame(X.toarray(), columns=vectorizador.get_feature_names_out())
    predicciones = predict_model(modelo, data=df)
    return predicciones['prediction_label'].iloc[0]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py <ruta_del_pdf>")
        sys.exit(1)

    ruta_archivo = os.path.abspath(sys.argv[1])  # Convertir a ruta absoluta
    if not os.path.exists(ruta_archivo):
        print(f"[ERROR] El archivo {ruta_archivo} no existe.")
        sys.exit(1)

    tipo_documento = procesar_archivo(ruta_archivo)
    print(f"El tipo de documento es: {tipo_documento}")

    # Definir carpeta temporal de manera segura
    output_dir = os.path.join(BASE_DIR, ".tmp")
    output_file = os.path.join(output_dir, "clasificacion.txt")

    # Asegurar que el directorio exista
    os.makedirs(output_dir, exist_ok=True)

    # Guardar el resultado en un archivo
    with open(output_file, 'w') as file:
        file.write("El tipo de documento es: " + tipo_documento)

    print(f"[INFO] Resultado guardado en {output_file}")
