from stanza import Pipeline
# Initialize Stanza pipelines for English and Arabic
nlp_en = Pipeline(lang='en', processors='tokenize,ner')
nlp_ar = Pipeline(lang='ar', processors='tokenize,ner')

def extract_locations(text, lang='en'):
    """
    Extract location entities from the given text using Stanza NLP library.

    Args:
        text (str): The input text from which to extract locations.
        lang (str): The language of the input text ('en' for English, 'ar' for Arabic).

    Returns:
        list: A list of extracted location entities.
    """
    if lang == 'en':
        doc = nlp_en(text)
    elif lang == 'ar':
        doc = nlp_ar(text)
    else:
        raise ValueError("Unsupported language. Use 'en' for English or 'ar' for Arabic.")

    locations = set()
    for sentence in doc.sentences:
        for ent in sentence.ents:
            if ent.type in {'GPE', "LOC", "FAC", "ORG"}: # GPE: Geo-Political Entity, LOC: Location, FAC: Facility, ORG: Organization
                locations.add(ent.text)
    return locations