import torch
import mylib
from transformers import BertTokenizerFast, EncoderDecoderModel
device = 'cuda' if torch.cuda.is_available() else 'cpu'
ckpt = 'mrm8488/bert2bert_shared-spanish-finetuned-summarization'
tokenizer = BertTokenizerFast.from_pretrained(ckpt)
model = EncoderDecoderModel.from_pretrained(ckpt).to(device)

def generate_summary(text):
    inputs = tokenizer([text], padding="max_length", truncation=True, max_length=512, return_tensors="pt")
    input_ids = inputs.input_ids.to(device)
    attention_mask = inputs.attention_mask.to(device)
    
    # Ajustar estos parámetros según sea necesario
    output = model.generate(
        input_ids, 
        attention_mask=attention_mask,
        max_length=400,  # Aumenta la longitud máxima del resumen
        min_length=150,   # Establece una longitud mínima para el resumen
        length_penalty=2.0,  # Penaliza las salidas cortas para favorecer resúmenes más largos
        no_repeat_ngram_size=3,  # Evita la repetición de n-gramas para mejorar la calidad del texto
        early_stopping=True  # Detiene la generación temprano si todas las secuencias alcanzan el token de fin
    )
    return tokenizer.decode(output[0], skip_special_tokens=True)

   
text = mylib.corregir_erratas_texto(mylib.extraer_texto_pdf('/Users/administrador/AFE/circulares/005-01.pdf'))
print (generate_summary(text))
