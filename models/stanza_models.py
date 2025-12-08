import stanza

_models = {}
_langugages = ['en', 'ar']

for lang_code in _langugages:
    stanza.download(lang_code)
    
def get_model(lang):
    if lang not in _langugages:
        raise ValueError(f"Language '{lang}' is not supported.")
    if lang not in _models:
        _models[lang] = stanza.Pipeline(lang=lang, processors='tokenize,mwt,ner')
    return _models[lang]
