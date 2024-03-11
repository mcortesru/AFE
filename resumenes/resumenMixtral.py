import replicate
import mylib

text = mylib.corregir_erratas_texto(mylib.extraer_texto_pdf())

output = replicate.run(
    "meta/llama-2-70b-chat",
    input={
        "debug": False,
        "top_p": 1,
        "prompt": "Haz un resumen en español de este texto:\n\n" + text,
        "temperature": 0.5,
        "system_prompt": "Haz un resumen en español",
        "max_new_tokens": 500,
        "min_new_tokens": -1
    }
)
print(''.join(output))