from extracters.abc_extractor import ABCExtractor
from models.stanza_models import get_model
from dateparser.search import search_dates


class MultiLangTemporalExtractor(ABCExtractor):
    def extract(self, text, lang='en'):
        self._validate_text(text)
        temporal_set = set()

        if lang == 'en':
            # Use Stanza for English
            nlp = get_model(lang)
            doc = nlp(text)
            for ent in doc.ents:
                if ent.type in {'DATE', 'TIME', 'DURATION', 'SET'}:
                    temporal_set.add(ent.text)
        elif lang == 'ar':
            # Use dateparser for Arabic
            result = search_dates(text, languages=['ar'])
            if result:
                temporal_set = {match[0] for match in result}

        return temporal_set


