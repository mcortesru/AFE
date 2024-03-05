
import spacy
from spacy.training import Example
import random



# Carga el modelo de lenguaje
nlp = spacy.load("es_core_news_sm")

# Añade el componente 'textcat' si aún no está en el pipeline
if 'textcat' not in nlp.pipe_names:
    config = {
        "threshold": 0.5,
        "model": {
            "@architectures": "spacy.TextCatBOW.v1",
            "exclusive_classes": True,
            "ngram_size": 1,
            "no_output_layer": False
        }
    }
    textcat = nlp.add_pipe("textcat", last=True, config=config)
else:
    textcat = nlp.get_pipe("textcat")

# Añade las etiquetas al componente 'textcat'
textcat.add_label("positivo")
textcat.add_label("negativo")

# Datos de entrenamiento
train_data = [
    ("Me encanta este producto", {"cats": {"positivo": True, "negativo": False}}),
    ("Es el peor servicio que he recibido", {"cats": {"positivo": False, "negativo": True}}),
    ("Me encanta este producto", {"cats": {"positivo": True, "negativo": False}}),
    ("Es el peor servicio que he recibido", {"cats": {"positivo": False, "negativo": True}}),
    ("Una experiencia increíble, totalmente recomendado", {"cats": {"positivo": True, "negativo": False}}),
    ("Estoy decepcionado con la calidad del producto", {"cats": {"positivo": False, "negativo": True}}),
    ("El servicio al cliente superó mis expectativas", {"cats": {"positivo": True, "negativo": False}}),
    ("La comida estaba fría y tardó mucho en llegar", {"cats": {"positivo": False, "negativo": True}}),
    ("Excelente calidad a un precio razonable", {"cats": {"positivo": True, "negativo": False}}),
    ("El artículo llegó dañado y el reembolso fue complicado", {"cats": {"positivo": False, "negativo": True}}),
    ("Un servicio al cliente amable y eficiente", {"cats": {"positivo": True, "negativo": False}}),
    ("El producto no cumple con las especificaciones anunciadas", {"cats": {"positivo": False, "negativo": True}}),
    ("Rápido, eficaz y fácil de usar. Estoy muy satisfecho", {"cats": {"positivo": True, "negativo": False}}),
    ("Frustrante experiencia de usuario, esperaba mucho más", {"cats": {"positivo": False, "negativo": True}}),
    ("El mejor en su categoría, no cambiaría por otro", {"cats": {"positivo": True, "negativo": False}}),
    ("Mala relación calidad-precio", {"cats": {"positivo": False, "negativo": True}}),
    ("Atención personalizada y detallista", {"cats": {"positivo": True, "negativo": False}}),
    ("No vale la pena el dinero que cuesta", {"cats": {"positivo": False, "negativo": True}}),
    ("Sobresaliente en todos los aspectos", {"cats": {"positivo": True, "negativo": False}}),
    ("Una completa pérdida de tiempo y recursos", {"cats": {"positivo": False, "negativo": True}}),
]

# Convierte los datos de entrenamiento a ejemplos de SpaCy
train_examples = [Example.from_dict(nlp.make_doc(text), cats) for text, cats in train_data]

# Entrenamiento del modelo
optimizer = nlp.initialize()
for i in range(10):
    random.shuffle(train_examples)
    for batch in spacy.util.minibatch(train_examples, size=2):
        nlp.update(batch, sgd=optimizer)

# Prueba el clasificador con un nuevo texto
doc = nlp("Es muy malo")
print(doc.cats)

