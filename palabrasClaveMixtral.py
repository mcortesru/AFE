import replicate
import mylib
import sys
import io

# export REPLICATE_API_TOKEN=r8_NR3kLxhtZqIte3dMARbxiQthIBAi2jf4QWhTy
# export REPLICATE_API_TOKEN=r8_9P0pn1CqVUQwidMfCVO8vVhB0GZCtSJ2x2UD0

output_buffer = io.StringIO()
sys.stdout = output_buffer


if len(sys.argv) < 2:
    # path_al_archivo = input("No se ha proporcionado el path del archivo. Por favor, introduce el path del archivo: ")   
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-147.pdf" 
     path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-68-69.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-71.pdf"
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/005-11-30-33.pdf"  # MUY LARGO
    # path_al_archivo = "/Users/administrador/Desktop/PDFs/ACTAS/004-07-165-168.pdf"
else:
    path_al_archivo = sys.argv[1]

try:
    text = mylib.extraer_texto_pdf(path_al_archivo)
except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    sys.exit(1)

print("Texto extraído del archivo:")
print(text)

print("Haciendo petición a la API de palabras clave...")
print()


input = {
    "top_p": 0.95,
    "top_k": 30,
    "prompt": "Extrae las palabras clave del siguiente texto:\n\n" + text,
    "temperature": 0.3,
    "presence_penalty": 0.1,
    "frequency_penalty": 0.1,
    "max_tokens": 70
}


for event in replicate.stream(
    "meta/meta-llama-3-8b-instruct",
    input=input
): 
    print(event, end="")


sys.stdout = sys.__stdout__

output = output_buffer.getvalue()
output_captured = output_buffer.getvalue()
print(output_captured)
output_buffer.close()

keywords = [line.strip() for line in output.split('\n') if line.strip().startswith('* ')]
keywords = [keyword[2:].strip() for keyword in keywords]

if keywords:
    keywords.pop()

print(keywords)

