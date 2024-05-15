import sys
import replicate
import mylib

# export REPLICATE_API_TOKEN=r8_NR3kLxhtZqIte3dMARbxiQthIBAi2jf4QWhTy
# export REPLICATE_API_TOKEN=r8_9P0pn1CqVUQwidMfCVO8vVhB0GZCtSJ2x2UD0

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


input={
        "debug": False,
        "top_p": 1,
        "prompt": "Hazme un resumen de este documento: \n\n" + text,
        "temperature": 0.5,
        "system_prompt": "Resumir un texto en español",
        "max_new_tokens": 500,
        "min_new_tokens": -1,
        "tokens": 1000,
    }


for event in replicate.stream(
    "meta/meta-llama-3-8b-instruct",
    input=input
): 
    print(event, end="")

print()
