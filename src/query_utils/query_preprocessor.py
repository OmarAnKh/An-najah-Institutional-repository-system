import re
from typing import Iterable, List

from sentence_transformers import SentenceTransformer
from langdetect import detect

from src.extracters.geopy_geo_location_finder import GeopyGeoLocationFinder
from src.extracters.stanza_temporal_extractor import MultiLangTemporalExtractor
from src.extracters.stanza_locations_extractor import StanzaLocationsExtractor

from global_config import global_config

BAD_LOCATION_WORDS = {
    "management",
    "system",
    "model",
    "project",
    "strategy",
    "analysis",
    "spss",
    "tam",
    "tpb",
    "pma",
    "csr",
}

YEAR_RE = re.compile(r"(19|20)\d{2}")

# Create instances of your extractors and geo location finders
geo_finder = GeopyGeoLocationFinder()
temporal_extractor = MultiLangTemporalExtractor()
locations_extractor = StanzaLocationsExtractor()

# Load embedding model once
vector_model = SentenceTransformer(global_config.embedding_model_name)


def filter_safe_temporals(temporals: Iterable[str] | None) -> List[str]:
    """
    Keep only year-like temporals:
    - "2014"
    - "2013-2019" (range)
    Drops things like "winter", "recent years", "90%", ages, durations, etc.
    """
    if not temporals:
        return []

    out: List[str] = []
    for t in temporals:
        t = (str(t) or "").strip()
        if not t:
            continue

        # drop obvious junk
        if "%" in t:
            continue

        # keep if contains a year (2014) or a year range (2013-2019)
        if YEAR_RE.search(t):
            out.append(t)

    return out


def strip_year_like_tokens(text: str) -> str:
    """Remove standalone year tokens and common year-range patterns from text."""
    if not text:
        return ""
    t = text

    # Remove ranges like 2013-2019
    t = re.sub(r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b", " ", t)

    # Remove forms like 2013 to 2019 / 2013–2019
    t = re.sub(
        r"\b(19|20)\d{2}\s*(to|until|till)\s*(19|20)\d{2}\b",
        " ",
        t,
        flags=re.IGNORECASE,
    )

    # Remove standalone years
    t = re.sub(r"\b(19|20)\d{2}\b", " ", t)

    t = re.sub(r"\s+", " ", t).strip()
    return t


def expand_year_ranges(temporals: List[str]) -> List[str]:
    """
    Convert tokens like '2013-2019' into ['2013','2014',...,'2019'].
    Keeps normal year tokens as-is.
    """
    out: List[str] = []
    for t in temporals or []:
        t = str(t).strip()
        m = re.fullmatch(r"(19|20)\d{2}\s*-\s*(19|20)\d{2}", t)
        if m:
            start = int(t.split("-")[0].strip())
            end = int(t.split("-")[1].strip())
            if start <= end and (end - start) <= 50:
                out.extend([str(y) for y in range(start, end + 1)])
            else:
                out.append(t)
        else:
            out.append(t)
    # unique, keep order
    seen = set()
    deduped = []
    for x in out:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    return deduped


def build_lexical_text(query: str, temporals, locations) -> str:
    """
    Option A (token-aware lexical anchoring):
      - KEEP locations in the BM25 text (prevents generic drift).
      - REMOVE ALL year-like temporals from the BM25 MUST text (years can hijack ranking).
      - Years/ranges are handled only as SOFT boosts elsewhere (temporalExpressions).
    """
    # We still remove only "noisy temporals" phrases that are not simple years (e.g., 'recent years')
    safe_temporals = set(expand_year_ranges(filter_safe_temporals(temporals)))

    temporals_set = set((str(t) or "").strip() for t in (temporals or []))
    noisy_temporals = [t for t in temporals_set if t and t not in safe_temporals]

    # Remove noisy temporal phrases, but keep locations
    text = clean_query_text(
        query=query,
        temporal_expressions=noisy_temporals,
        locations=[],
    )

    # Critical: remove year-like tokens from the lexical anchor
    text = strip_year_like_tokens(text)

    return text


def is_probable_location(name: str) -> bool:
    t = (name or "").strip()
    if not t:
        return False
    if len(t) <= 2:
        return False
    # block acronyms like WB, SPSS, TAM
    if t.isupper() and len(t) <= 6:
        return False
    low = t.lower()
    if any(w in low for w in BAD_LOCATION_WORDS):
        return False
    return True


def clean_query_text(
    query: str,
    temporal_expressions: Iterable[str] | None = None,
    locations: Iterable[str] | None = None,
) -> str:
    """
    Remove extracted temporal expressions and location names
    from the query text, keeping it readable and safe for BM25/embeddings.
    """
    text = query or ""

    phrases = set()

    if temporal_expressions:
        phrases.update(t.strip() for t in temporal_expressions if t)

    if locations:
        phrases.update(l.strip() for l in locations if l)

    # remove longer phrases first (important!)
    for phrase in sorted(phrases, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        text = pattern.sub(" ", text)

    # clean up whitespace & punctuation
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    return text


def extractors(q: str, lang: str):

    temporals = temporal_extractor.extract(q, lang=lang)
    locations = locations_extractor.extract(q, lang=lang)

    geo_refs = []
    for location in locations:
        if not is_probable_location(location):
            continue

        geo = geo_finder._geocode_single_place(location)
        if not geo:
            continue

        geo_refs.append(
            {
                "placeName": geo.placeName,
                "lat": geo.coordinates.lat,
                "lon": geo.coordinates.lon,
            }
        )

        if len(geo_refs) >= 3:
            break

    return temporals, geo_refs, locations


def prepare_input(q):

    lang = detect(q)
    if lang not in ("en", "ar"):
        lang = "en"

    temporals, geo_refs, locations = extractors(q, lang)

    semantic_clean_query = clean_query_text(
        query=q,
        temporal_expressions=temporals,
        locations=locations,
    )

    lexical25_clean_query = build_lexical_text(q, temporals, locations)

    emb = vector_model.encode([semantic_clean_query])[0]
    semantic_vector = emb.tolist() if hasattr(emb, "tolist") else list(emb)

    return lang, lexical25_clean_query, semantic_vector, temporals, geo_refs
