import torch
# import mylib
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

   
text = """.. 
Madrid , 12-2-66 
Mi ; querida gente: 
Frescos sois bastante~Por todas partes me dicen que si la censura ••• que si me 
cepillan ••• Y vosotros ni palabra.Pero hombre ••• 
De verdad me interesa por muchos motivos saber lo que pas6. Mandadme 
los artículos originales si es posible todavía.Me vendrán muy bien. 
No se Bi se salieron o no.Y có~o salieron.No recibí más que un número el 
18 de diciembre • 
Desde luego,si esas cosas tan suaves y finas no pasan por el hocico de los 
católicos cancerberos que sufrimos,no hay que tener esperanzas en nada. 
Supongo que SIGNO no estará dispuesto a forcejear ni a cambiar ruta.Pero 
en esto ahora no me voy a meter. Es otra grave cuestión. 
Además también supongo que en caso de denunciarme a mi obispo,si no lo han 
hecho ya, nadie saldría a romper una lanza. Por lo tanto , si las cosas son así, 
yo no puedo seguir escribiendo en JUVENTUD OBRERA, que por ahora no tiene cen 
sura he comenzado una serie parecida a la otra,pero de otro tipo. 
Si quereis y antes de que me lie con otra publicación escribiré encantado 
en otro nivel , por ejemplo una sección mensual ,breve,actual ,"incisiva" sobre 
algún aspecto de la Iglesia en el mundo . Podria empezar por la prensa,si es 
que ya el tema no lo habeis manido . 
Espero vuestra,aunque lenta , esperada palabra . 
Cordialmente"""
print (generate_summary(text))
