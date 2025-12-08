from abc import ABC, abstractmethod
import spacy
import re

class TemporalExpressionExtractor(ABC):

    @abstractmethod
    def extract_temporal_expressions(self, text):
        pass


class SpacyTemporalExtractor(TemporalExpressionExtractor):

    nlp = spacy.load("en_core_web_sm")

    # Define months (Arabic + English)
    arabic_months = ["يناير", "فبراير", "مارس", "أبريل", "ابريل", "مايو", "يونيو", "يوليو",
                     "أغسطس", "اغسطس", "سبتمبر", "أكتوبر", "اكتوبر", "نوفمبر", "ديسمبر"]
    english_months = ["January", "February", "March", "April", "May", "June", "July", "August",
                      "September", "October", "November", "December"]
    all_months = [m.lower() for m in arabic_months + english_months]

    # Regex for years
    year_regex = r"(\d{4}|[٠-٩]{4})"

    def extract_temporal_expressions(self, text):
        results = []
        doc = self.nlp(text)

        for sentence in doc.sents:
            sent_text = sentence.text

            # Find months
            month_matches = [(m.start(), m.group()) for m in re.finditer(r'\b\w+\b', sent_text)
                             if m.group().lower() in self.all_months]

            # Find years
            year_matches = [(y.start(), y.group()) for y in re.finditer(self.year_regex, sent_text)]

            # Merge months and years
            month_index = year_index = 0
            while month_index < len(month_matches) or year_index < len(year_matches):
                if month_index < len(month_matches) and (year_index >= len(year_matches)
                                                         or month_matches[month_index][0] < year_matches[year_index][0]):
                    month = month_matches[month_index][1]
                    year = None
                    if year_index < len(year_matches) and year_matches[year_index][0] > month_matches[month_index][0]:
                        year = year_matches[year_index][1]
                        year_index += 1
                    results.append({ "month": month, "year": year})
                    month_index += 1
                elif year_index < len(year_matches):
                    year = year_matches[year_index][1]
                    next_month = None
                    if month_index < len(month_matches) and month_matches[month_index][0] > year_matches[year_index][0]:
                        next_month = month_matches[month_index][1]
                        month_index += 1
                        results.append({ "month": next_month, "year": year})
                    else:
                        results.append({"month": None, "year": year})
                    year_index += 1
        return results


