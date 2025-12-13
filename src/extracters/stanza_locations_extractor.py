from src.extracters.abstract_classes.abc_extractor import ABCExtractor
from src.models.stanza_models import get_model


class StanzaLocationsExtractor(ABCExtractor):
    """
    Extracts location names from text using Stanza NLP library.
    Locations include geopolitical entities, facilities, and organizations.
    """

    def extract(self, text, lang="en"):
        """
        extract location names from a given text.

        Args:
            text (str): The input text from which to extract location names.
            lang (str, optional): The language of the input text. Defaults to 'en'.

        Returns:
            set: A set of extracted location names.
        """
        self._validate_text(text)
        nlp = get_model(lang)
        doc = nlp(text)
        locations = set()
        for ent in doc.ents:
            if ent.type in {
                "GPE",
                "LOC",
                "FAC",
                "ORG",
            }:  # GPE stands for Geo-Political Entity, LOC for Location, FAC for Facility, ORG for Organization
                locations.add(ent.text)
        return locations
