import mylib

# Ejemplo de texto
text = mylib.extraer_texto_pdf("/Users/administrador/Desktop/PDFs/CARTAS/ACE_JAC_9A_07-71.pdf")

from flair.data import Sentence
from flair.models import SequenceTagger

# load tagger
tagger = SequenceTagger.load("flair/ner-spanish-large")

# convert text to a Sentence object
sentence = Sentence(text)

# predict NER tags
tagger.predict(sentence)

# print sentence
print(sentence)

# print predicted NER spans
print('The following NER tags are found:')
# iterate over entities and print
for entity in sentence.get_spans('ner'):
    print(entity)