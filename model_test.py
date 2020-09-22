import os
import tensorflow as tf
model_file = os.path.dirname(os.path.abspath(__file__))
# print(model_file)
model_file = os.path.join(model_file, "models/taxon_model")
# print(model_file)
model = tf.keras.models.load_model(model_file)

lst_of_samples = [
    ['Mastocarpus stellatus'],
    ['Prasiola calophylla'],
    ['unicellular organisms'],
    ['red algae'],
    ['separating embryophytes'],
    ['Ulva intestinalis'],
    ['Buccinum undatum'],
    ['Oxymonacanthus longirostris'],
    ['molecular spectroscopy'],
    ['Briareum sp.']
]
for s in lst_of_samples:
    res = model.predict(s)
    print(res[0][0])
