from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import mylib
tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large-finetuned-conll03-english")
model = AutoModelForTokenClassification.from_pretrained("xlm-roberta-large-finetuned-conll03-english")
classifier = pipeline("ner", model=model, tokenizer=tokenizer)
text_to_classify = mylib.corregir_erratas_texto(mylib.extraer_texto_pdf())
results = classifier(text_to_classify)

# Print out the classification results
for entity in results:
    print(f"Entity: {entity['word']}, Label: {entity['entity']}, Score: {entity['score']:.4f}, Index: {entity['index']}")