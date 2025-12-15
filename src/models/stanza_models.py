import stanza

# Dictionary to hold loaded models
# Key: language code, Value: Stanza NLP pipeline
_models = {}
# Supported languages
_languages = ["en", "ar"]


def _ensure_model(lang: str) -> None:
    """Download model for lang if missing; no-op when already present."""
    stanza.download(lang, verbose=False)


def get_model(lang):
    """
    Get the Stanza NLP model for the specified language.
    Args:
        lang (str): The language code for the desired model.

    Returns:
        stanza.Pipeline: The Stanza NLP pipeline for the specified language.

    Raises:
        ValueError: If the specified language is not supported.
    """
    if lang not in _languages:
        raise ValueError(f"Language '{lang}' is not supported.")
    if lang not in _models:
        _ensure_model(lang)
        _models[lang] = stanza.Pipeline(lang=lang, processors="tokenize,mwt,ner")
    return _models[lang]
