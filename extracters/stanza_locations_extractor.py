from extracters.abc_extractor import ABCExtractor
from models.stanza_models import get_model

class StanzaLocationsExtractor(ABCExtractor):
    def extract(self, text, lang = 'en'):
        self._validate_text(text)
        nlp = get_model(lang)
        doc = nlp(text)
        locations = set()
        for ent in doc.ents:
            if ent.type in {'GPE', 'LOC', 'FAC', 'ORG'}:  # GPE stands for Geo-Political Entity, LOC for Location, FAC for Facility, ORG for Organization
                locations.add(ent.text)
        return locations