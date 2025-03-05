from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import subprocess
from werkzeug.utils import secure_filename
import os
import sys
import logging
from chromadb_open import chatbot_inicializar, chat


logging.basicConfig(level=logging.DEBUG)
print("Iniciando Flask...")

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Necesario para manejar sesiones
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def resumen(temp_path):
    print("Ejecutando resumen...")
    result = subprocess.run(['python', '../resumen.py', temp_path], capture_output=True, text=True)
    if result.stderr:
        print("Error al ejecutar el script de resumen:", result.stderr)
    return result.stdout if result.stdout else f"No se pudo obtener un resumen. Error: {result.stderr}"

def clasificacion (temp_path):
    print ("Clasificando el documento...")
    file_path = '/tmp/clasificacion.txt'

    result = subprocess.run(['python', '../clasificador.py', temp_path], text=True)
    if result.stderr:
        print("Error al ejecutar el script de clasificación:", result.stderr)
        return f"No se pudo obtener la clasificación. Error: {result.stderr}"
    
    if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                clas_results = file.read()
            os.remove(file_path)
            return clas_results if clas_results else "No se pudo clasificar el documento"
    else:
        return "El archivo de resultados no se encontró o no se pudo crear."

def tokens(temp_path):
    print("Obteniendo los NERs del documento...")
    file_path = '/tmp/NERS.txt'  # La misma ruta fija que NER.py usa para escribir

    result = subprocess.run(['python', '../NER.py', temp_path], text=True)  # Ejecutar NER.py sin argumentos de ruta

    if result.stderr:
        print("Error al ejecutar el script de obtención de NERs:", result.stderr)
        return f"No se pudieron obtener los NERs. Error: {result.stderr}"

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            ner_results = file.read()
        os.remove(file_path)
        return ner_results if ner_results else "No se encontraron NERs."
    else:
        return "El archivo de resultados no se encontró o no se pudo crear."

def palabras (temp_path):
    print ("Obteniendo palabras clave del documento...")
    result = subprocess.run(['python', '../palabras.py', temp_path], capture_output=True, text=True)
    if result.stderr:
        print("Error al ejecutar el script de palabras clave:", result.stderr)
    return result.stdout if result.stdout else f"No se pudo obtener las palabras clave. Error: {result.stderr}"


@app.route('/')
def index():
    print("Cargando la página principal...")
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    button_id = request.form.get('buttonId')
    file = request.files.get('file')
    
    print(f"[DEBUG] buttonId recibido: {button_id}")  # Agrega esta línea
    print(f"[DEBUG] Archivo recibido: {file.filename if file else 'Ninguno'}")  # Esta línea muestra
    
    if not file:
        return jsonify({"error": "No se recibió ningún archivo"}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join('/tmp', filename)
    file.save(temp_path)

    message = "Acción no reconocida."

    if button_id == 'resumen':
        message = resumen(temp_path)
    elif button_id == 'clasificacion':
        message = clasificacion(temp_path)
    elif button_id == 'tokens':
        message = tokens(temp_path)
    elif button_id == 'palabras':
        message = palabras(temp_path)
    elif button_id == 'chatbot':
        # Inicializar el chatbot con el documento subido
        if chatbot_inicializar(temp_path):
            session['current_document'] = temp_path  # Guardamos en la sesión
            session.modified = True  # Forzar la actualización de la sesión
            message = f"Chatbot inicializado con {filename}."
        else:
            message = "No se pudo procesar el documento para el chatbot."

    return jsonify({"message": message})

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """Recibe una pregunta en JSON y devuelve la respuesta del chatbot."""
    if 'current_document' not in session:
        return jsonify({"error": "No se ha subido ningún documento."}), 400

    data = request.json
    pregunta = data.get("message", "").strip()

    if not pregunta:
        return jsonify({"error": "No se proporcionó ninguna pregunta."}), 400

    respuesta = chat(pregunta)  # Llamamos a la función del chatbot
    return jsonify({"response": respuesta})

if __name__ == '__main__':
    app.run(debug=True)