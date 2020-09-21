import tensorflow as tf

model_file= '/Users/trinhsk/Documents/gitrepos/nlpPDFNN_app/models/taxon_model'
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
