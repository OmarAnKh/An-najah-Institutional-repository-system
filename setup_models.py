import stanza

# Download the English and Arabic models for the Stanza NLP library
# you should run this only once so that the models are downloaded to your system
stanza.download("en")
stanza.download("ar")  