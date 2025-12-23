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
    Filter extracted temporals to keep only year-like values.

    Keeps:
    - Single years like "2014"
    - Year ranges like "2013-2019"

    Drops:
    - Seasons (e.g., "winter")
    - Relative phrases (e.g., "recent years")
    - Percentages, ages, and other non-year temporals

    Args:
        temporals: Iterable of extracted temporal strings.

    Returns:
        A list of temporal strings that contain a 4-digit year pattern.
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
    """
    Remove year-like tokens and common year-range patterns from text.

    This is used to prevent standalone years (e.g., "2014") and ranges
    (e.g., "2013-2019", "2013 to 2019") from dominating lexical BM25 ranking.
    The semantic/temporal handling is done elsewhere via soft boosts.

    Args:
        text: Input query string.

    Returns:
        Text with year tokens and year-range patterns removed and whitespace normalized.
    """
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
    Expand year ranges into individual year tokens while preserving order.

    Example:
        "2013-2015" -> ["2013", "2014", "2015"]

    Safety:
        Expansion is limited to ranges of length <= 50 years to avoid blowups.

    Args:
        temporals: List of temporal strings (years and/or ranges).

    Returns:
        A de-duplicated list of year tokens and/or original temporals.
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
    Build the lexical BM25 query text using Option A (token-aware anchoring).

    Strategy:
    - Keep location mentions inside the lexical text to anchor retrieval.
    - Remove year-like tokens/ranges from the lexical text to avoid ranking hijack.
    - Keep non-year temporal phrases removable via `clean_query_text` (when applicable).
    - Temporal constraints are handled later as *soft boosts* (not hard filters).

    Args:
        query: Raw user query text.
        temporals: Extracted temporal expressions from the query.
        locations: Extracted location mentions from the query.

    Returns:
        A cleaned lexical query string for BM25 matching.
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
    """
    Heuristically decide whether a string is a plausible location mention.

    Used as a lightweight guard before geocoding to reduce noise and avoid
    unnecessary geocoding calls. It filters out:
    - Very short fragments
    - Short uppercase acronyms (e.g., "SPSS", "TAM")
    - Tokens containing known non-location keywords (e.g., "model", "analysis")

    Args:
        name: A candidate location phrase extracted from the query.

    Returns:
        True if the phrase looks like a plausible place name, otherwise False.
    """

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
    Remove extracted temporals and locations from a query string.

    This is mainly used to produce a cleaner semantic input (for embeddings)
    by removing explicit temporal/location mentions after they have been
    extracted and will be handled separately (e.g., boosting/filtering).

    Args:
        query: Raw query text.
        temporal_expressions: Extracted temporal phrases to remove.
        locations: Extracted location phrases to remove.

    Returns:
        Cleaned query text with removed phrases and normalized whitespace.
    """
    text = query or ""

    phrases = set()

    if temporal_expressions:
        for temp in temporal_expressions:
            if temp:
                phrases.add(temp.strip())

    if locations:
        for loc in locations:
            if loc:
                phrases.add(loc.strip())

    # remove longer phrases first to avoid partial overlaps
    for phrase in sorted(phrases, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        text = pattern.sub(" ", text)

    # clean up whitespace & punctuation
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    return text


def extractors(q: str, lang: str):
    """
    Extract temporals and locations from a query and build structured geo references.

    Steps:
    - Extract temporal expressions using the configured temporal extractor.
    - Extract location candidates using the configured locations extractor.
    - Optionally geocode up to 3 plausible locations into structured geo refs:
      {"placeName": ..., "lat": ..., "lon": ...}.

    Args:
        q: Raw user query text.
        lang: Query language ("en" or "ar") used for the NLP extractors.

    Returns:
        A tuple in the exact order:
            temporals: List of extracted temporal expressions.
            geo_refs: List of structured geo references (up to 3).
            locations: List of extracted location surface forms.
    """

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
    """
    Prepare a raw user query for hybrid retrieval (lexical + semantic + signals).

    This function:
    - Detects the query language ("en"/"ar") using `langdetect`.
    - Extracts temporal expressions and geo references from the query.
    - Builds:
        - A semantic-clean query (temporals/locations removed) for embeddings.
        - A lexical BM25 query text using Option A (locations kept, years stripped).
    - Encodes the semantic-clean query into an embedding vector.

    Args:
        q: Raw user query text.

    Returns:
        A 5-tuple in the exact order:
            lang: Resolved language ("en" or "ar").
            lexical25_clean_query: Lexical BM25 query text.
            semantic_vector: Embedding vector as a Python list[float].
            temporals: Extracted temporal expressions.
            geo_refs: Structured geo references (list of dicts).
    """

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
