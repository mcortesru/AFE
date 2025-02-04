from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app)


def resumen(temp_path):
    print("Ejecutando resumen...")
    result = subprocess.run(['python', '../resumen.py', temp_path], capture_output=True, text=True)
    if result.stderr:
        print("Error al ejecutar el script de resumen:", result.stderr)
    return result.stdout if result.stdout else f"No se pudo obtener un resumen. Error: {result.stderr}"

def clasficacion (temp_path):
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