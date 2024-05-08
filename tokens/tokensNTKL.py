import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from collections import defaultdict

nlp_spacy = spacy.load("es_core_news_sm")

text = ""

def analizar_texto_nltk(texto):
    tokens = word_tokenize(texto)
    tags = pos_tag(tokens)
    arbol_entidades = ne_chunk(tags)
    
    entidades = []
    for subtree in arbol_entidades:
        if type(subtree) == nltk.Tree:
            entidad = " ".join([token for token, pos in subtree.leaves()])
            entidades.append(entidad)
    return entidades

def analizar_texto_spacy(texto):
    doc = nlp_spacy(texto)
    entidades = [ent.text for ent in doc.ents]
    return entidades

def cruzar_resultados(texto):
    entidades_nltk = analizar_texto_nltk(texto)
    entidades_spacy = analizar_texto_spacy(texto)
    
    # Conversión a sets para facilitar la intersección
    entidades_nltk_set = set(entidades_nltk)
    entidades_spacy_set = set(entidades_spacy)
    
    # Intersección de ambos sets para obtener coincidencias
    entidades_coincidentes = entidades_nltk_set.intersection(entidades_spacy_set)
    
    return entidades_coincidentes


# Obtiene las entidades coincidentes entre NLTK y spaCy
entidades_coincidentes = cruzar_resultados(text)

print("Tokens obtenidos del texto:")
for entidad in entidades_coincidentes:
    print(entidad)