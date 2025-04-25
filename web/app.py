import os
import subprocess
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging
from chromadb_open import chatbot_inicializar, chat
import sys
from dotenv import load_dotenv


logging.basicConfig(level=logging.DEBUG)
print("Iniciando Flask...")
load_dotenv()
flask_port = int(os.getenv("FLASK_PORT", 5002))
app = Flask(__name__)
CORS(app)

# Asegurar que la carpeta de uploads existe
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Crear carpeta temporal si no existe
TMP_DIR = os.path.join(os.path.dirname(__file__), "..", ".tmp")
os.makedirs(TMP_DIR, exist_ok=True)

if sys.platform == "win32":
    VENV_PYTHON = os.path.join(os.path.dirname(__file__), '..', 'mi_entorno', 'Scripts', 'python.exe')
else:
    VENV_PYTHON = os.path.join(os.path.dirname(__file__), '..', 'myenv', 'bin', 'python')

def resumen(temp_path):
    """Ejecuta el script de resumen en el entorno virtual."""
    print("Ejecutando resumen...")

    resumen_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resumen.py'))
    
    result = subprocess.run([VENV_PYTHON, resumen_script, temp_path], capture_output=True, text=True)

    if result.stderr:
        print("Error al ejecutar el script de resumen:", result.stderr)

    return result.stdout if result.stdout else f"No se pudo obtener un resumen. Error: {result.stderr}"


def clasificacion(temp_path):
    """Ejecuta el script de clasificación en el entorno virtual."""
    print("Clasificando el documento...")

    clasificador_script = os.path.join(os.path.dirname(__file__), '..', 'clasificador.py')
    file_path = os.path.join(TMP_DIR, 'clasificacion.txt')

    result = subprocess.run([VENV_PYTHON, clasificador_script, temp_path], capture_output=True, text=True)

    if result.stderr:
        print("Error al ejecutar el script de clasificación:", result.stderr)
        return f"No se pudo obtener la clasificación. Error: {result.stderr}"

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            clas_results = file.read()
        os.remove(file_path)
        return clas_results if clas_results else "No se pudo clasificar el documento."
    else:
        return "El archivo de resultados no se encontró o no se pudo crear."


def tokens(temp_path, threshold="0.99"):
    """Ejecuta el script de reconocimiento de entidades (NER) en el entorno virtual."""
    print("Obteniendo los NERs del documento...")

    ner_script = os.path.join(os.path.dirname(__file__), '..', 'NER.py')
    file_path = os.path.join(TMP_DIR, 'NERS.txt')

    result = subprocess.run([VENV_PYTHON, ner_script, temp_path, threshold], capture_output=True, text=True)

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


def palabras(temp_path):
    """Ejecuta el script de extracción de palabras clave en el entorno virtual."""
    print("Obteniendo palabras clave del documento...")

    palabras_script = os.path.join(os.path.dirname(__file__), '..', 'palabras.py')

    result = subprocess.run([VENV_PYTHON, palabras_script, temp_path], capture_output=True, text=True)

    if result.stderr:
        print("Error al ejecutar el script de palabras clave:", result.stderr)

    return result.stdout if result.stdout else f"No se pudo obtener las palabras clave. Error: {result.stderr}"

def ejecutar_chatbot_general_con_pregunta(pregunta):
    """Ejecuta el script chat_hibrido.py con una pregunta como argumento y devuelve todas las respuestas."""
    print(f"Ejecutando chatbot general con pregunta: {pregunta}")

    script_path = os.path.join(os.path.dirname(__file__), '.', 'chat_hibrido.py')
    result = subprocess.run(
        [VENV_PYTHON, script_path, pregunta],
        capture_output=True,
        text=True
    )

    # Capturar y mostrar la salida estándar y los errores
    if result.stdout:
        print(f"[DEBUG] Salida de chat_hibrido.py: {result.stdout}")
    if result.stderr:
        print(f"[ERROR] Error en chat_hibrido.py: {result.stderr}")

    if result.stderr:
        print("Error al ejecutar el chatbot general:", result.stderr)

    output = result.stdout

    # Extraer cada bloque de respuesta
    respuestas = {}
    bloques = ["SPACY", "CYPHER", "CHROMA", "COMBINADA"]
    for i, tag in enumerate(bloques):
        inicio = output.find(f"=== RESPUESTA {tag} ===")
        fin = output.find(f"=== RESPUESTA {bloques[i+1]} ===") if i + 1 < len(bloques) else len(output)
        if inicio != -1:
            respuestas[tag.lower()] = output[inicio + len(f"=== RESPUESTA {tag} ==="):fin].strip()

    return respuestas


@app.route('/')
def index():
    print("Cargando la página principal...")
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    file = request.files.get('file')
    button_id = request.form.get('buttonId')

    print(f"[DEBUG] buttonId recibido: {button_id}")
    print(f"[DEBUG] Archivo recibido: {file.filename if file else 'Ninguno'}")

    # Solo exigir archivo si no es chatbot-general
    if button_id != 'chatbot-general' and (not file or file.filename == ""):
        return jsonify({"error": "No se recibió ningún archivo"}), 400

    temp_path = None
    filename = None

    # Procesar el archivo si está presente y válido
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        temp_path = os.path.join(TMP_DIR, filename)
        file.save(temp_path)
        print(f"[DEBUG] Archivo guardado en: {temp_path}")
    else:
        print(f"[DEBUG] No se procesó ningún archivo (posiblemente innecesario)")

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
        if chatbot_inicializar(temp_path):
            session['current_document'] = temp_path
            session.modified = True
            message = f"Chatbot inicializado con {filename}."
        else:
            message = "No se pudo procesar el documento para el chatbot."
    elif button_id == 'chatbot-general':
        pregunta = request.form.get("question", "")
        if not pregunta:
            return jsonify({"error": "No se proporcionó ninguna pregunta"}), 400

        respuestas = ejecutar_chatbot_general_con_pregunta(pregunta)
        html_respuesta = ""
        for nombre, contenido in respuestas.items():
            html_respuesta += f"<h4 style='color:#4CAF50'>Respuesta {nombre.upper()}</h4><pre>{contenido}</pre><hr>"

        return jsonify({"message": html_respuesta})

    return jsonify({"message": message})


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    if 'current_document' not in session:
        return jsonify({"error": "No se ha subido ningún documento."}), 400

    data = request.json
    pregunta = data.get("message", "").strip()

    if not pregunta:
        return jsonify({"error": "No se proporcionó ninguna pregunta."}), 400

    respuesta = chat(pregunta)
    return jsonify({"response": respuesta})

@app.route('/chat-general', methods=['POST'])
def chat_general_endpoint():
    data = request.json
    pregunta = data.get("message", "").strip()

    if not pregunta:
        return jsonify({"error": "No se proporcionó ninguna pregunta."}), 400

    respuestas = ejecutar_chatbot_general_con_pregunta(pregunta)
    respuesta_texto = ""
    for nombre, contenido in respuestas.items():
        respuesta_texto += f"{nombre.upper()}:\n{contenido}\n\n"

    return jsonify({"response": respuesta_texto.strip()})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=flask_port)