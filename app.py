from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app)

@app.route('/process', methods=['POST'])
def process_file():
    button_id = request.form.get('buttonId')
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', filename)  # Path completo al archivo temporal
        file.save(temp_path)

        if button_id == 'resumen':
            message = resumen(temp_path)
        elif button_id == 'clasificacion':
            message = clasficacion(temp_path)
        elif button_id == 'tokens':
            message = tokens(temp_path)
        elif button_id == 'palabras':
            message = palabras(temp_path)
        else:
            message = "Acción no reconocida."
        
        os.remove(temp_path)

        return jsonify({"message": message})
    else:
        return jsonify({"message": "No se recibió ningún archivo"})



if __name__ == '__main__':
    app.run(debug=True)


def resumen(temp_path):
    print("Ejecutando resumen...")
    result = subprocess.run(['python', 'resumenMixtral.py', temp_path], capture_output=True, text=True)
    if result.stderr:
        print("Error al ejecutar el script de resumen:", result.stderr)
    return result.stdout if result.stdout else f"No se pudo obtener un resumen. Error: {result.stderr}"


def clasficacion (temp_path):
    return "Clasificando el documento..."

def tokens (temp_path):
    return "Obteniendo tokens del documento..."

def palabras (temp_path):
    return "Obteniendo palabras clave del documento..."
