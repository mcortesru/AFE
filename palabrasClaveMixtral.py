import replicate
import mylib
import sys

if len(sys.argv) < 2:
    print("No se ha proporcionado el path del archivo, se usará el de pruebas.")
    try:
        text = mylib.corregir_erratas_texto(mylib.extraer_texto_pdf())
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        sys.exit(1)

else:
    path_al_archivo = sys.argv[1]
    try:
        text = mylib.corregir_erratas_texto(mylib.extraer_texto_pdf(path_al_archivo))
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        sys.exit(1)

output = replicate.run(
    "meta/llama-2-70b-chat",
    input={
        "debug": False,
        "top_p": 1,
        "prompt": "Dame las palabras clave de este texto:\n\n" + text,
        "temperature": 0.5,
        "system_prompt": "Obtener palabras clave en español",
        "max_new_tokens": 10000,
        "min_new_tokens": -1
    }
)
print(''.join(output))

