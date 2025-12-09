from extracters.abc_extractor import ABCExtractor
from models.stanza_models import get_model
from dateparser.search import search_dates

"""
Extracts temporal expressions from text using Stanza NLP library for English and dateparser for Arabic.
Temporal expressions include dates, times, durations, and sets.
"""
class MultiLangTemporalExtractor(ABCExtractor):
    def extract(self, text, lang='en'):
        """
        Extract temporal expressions from a given text.

        Args:
            text (str): The input text from which to extract temporal expressions.
            lang (str, optional): The language of the input text. Defaults to 'en'.

        Returns:
            set: A set of extracted temporal expressions.
        """
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
        else:
            raise ValueError(f"Language '{lang}' is not supported.")

        return temporal_set


