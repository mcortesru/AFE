import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk

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

def analizar_texto_nltk(texto):
    tokens = word_tokenize(texto)
    tags = pos_tag(tokens)
    arbol_entidades = ne_chunk(tags, binary=False)
    
    entidades = []
    for subtree in arbol_entidades:
        if isinstance(subtree, nltk.Tree):
            entidad = " ".join(token for token, pos in subtree.leaves())
            tipo_entidad = subtree.label()  # NLTK provides the type of entity
            entidades.append((entidad, tipo_entidad))
    return entidades

# Get named entities with their types
entidades_con_tipos = analizar_texto_nltk(text)

# Print the entities and their types
print("Entities and their types from the text:")
for entidad, tipo in entidades_con_tipos:
    print(f"Entity: {entidad}, Type: {tipo}")
