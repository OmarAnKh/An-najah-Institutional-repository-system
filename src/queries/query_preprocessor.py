"""Query preprocessing utilities for hybrid search.

This module keeps the preprocessing lean while reusing the shared
extractors defined under :mod:`src.extracters`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from langdetect import detect
from sentence_transformers import SentenceTransformer

from global_config import global_config
from src.extracters.geopy_geo_location_finder import GeopyGeoLocationFinder
from src.extracters.stanza_locations_extractor import StanzaLocationsExtractor
from src.extracters.stanza_temporal_extractor import MultiLangTemporalExtractor

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
MAX_GEO_CANDIDATES = 3

geo_finder = GeopyGeoLocationFinder()
temporal_extractor = MultiLangTemporalExtractor()
locations_extractor = StanzaLocationsExtractor()
vector_model = SentenceTransformer(global_config.embedding_model_name)


@dataclass
class QuerySignals:
    """Normalized signals extracted from a user query."""

    temporals: List[str]
    geo_refs: List[Dict[str, float]]
    locations: List[str]


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def filter_safe_temporals(temporals: Iterable[str] | None) -> List[str]:
    """Keep only year-like temporal expressions."""

    if not temporals:
        return []

    return [t for t in (_clean_fragment(t) for t in temporals) if t and YEAR_RE.search(t)]


def strip_year_like_tokens(text: str) -> str:
    """Remove year numbers and common range patterns from text."""

    if not text:
        return ""

    cleaned = re.sub(r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b", " ", text)
    cleaned = re.sub(
        r"\b(19|20)\d{2}\s*(to|until|till)\s*(19|20)\d{2}\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\b(19|20)\d{2}\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def expand_year_ranges(temporals: Sequence[str]) -> List[str]:
    """Expand year ranges such as "2013-2015" into individual years."""

    expanded: List[str] = []
    for t in temporals or []:
        t = _clean_fragment(t)
        match = re.fullmatch(r"(19|20)\d{2}\s*-\s*(19|20)\d{2}", t)
        if not match:
            expanded.append(t)
            continue

        start, end = (int(x) for x in t.split("-"))
        if start <= end and (end - start) <= 50:
            expanded.extend(str(y) for y in range(start, end + 1))
        else:
            expanded.append(t)

    return _dedupe_preserve_order(expanded)


def clean_query_text(
    query: str,
    temporal_expressions: Iterable[str] | None = None,
    locations: Iterable[str] | None = None,
) -> str:
    """Strip explicit temporal/location mentions from text."""

    text = query or ""
    phrases = {
        _clean_fragment(p)
        for p in (temporal_expressions or [])
        if _clean_fragment(p)
    } | {
        _clean_fragment(l)
        for l in (locations or [])
        if _clean_fragment(l)
    }

    for phrase in sorted(phrases, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        text = pattern.sub(" ", text)

    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def build_lexical_text(query: str, temporals, locations) -> str:
    """Build BM25 text while stripping noisy temporal tokens."""

    safe_temporals = set(expand_year_ranges(filter_safe_temporals(temporals)))
    temporals_set = {_clean_fragment(t) for t in (temporals or []) if _clean_fragment(t)}
    noisy_temporals = [t for t in temporals_set if t not in safe_temporals]

    text = clean_query_text(query=query, temporal_expressions=noisy_temporals, locations=[])
    return strip_year_like_tokens(text)


def is_probable_location(name: str) -> bool:
    """Heuristically decide whether a string is likely a location mention."""

    t = _clean_fragment(name)
    if not t or len(t) <= 2:
        return False
    if t.isupper() and len(t) <= 6:
        return False
    low = t.lower()
    return not any(w in low for w in BAD_LOCATION_WORDS)


def extract_query_signals(q: str, lang: str) -> QuerySignals:
    """Run the configured extractors and geo coder once per query."""

    temporals = _dedupe_preserve_order(temporal_extractor.extract(q, lang=lang))
    locations = _dedupe_preserve_order(locations_extractor.extract(q, lang=lang))

    geo_refs: List[Dict[str, float]] = []
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
        if len(geo_refs) >= MAX_GEO_CANDIDATES:
            break

    return QuerySignals(temporals=temporals, geo_refs=geo_refs, locations=locations)


def prepare_input(q: str) -> Tuple[str, str, List[float], List[str], List[Dict[str, float]]]:
    """Prepare lexical/semantic inputs and extracted signals for search."""

    lang = detect(q)
    if lang not in ("en", "ar"):
        lang = "en"

    signals = extract_query_signals(q, lang)

    semantic_clean_query = clean_query_text(
        query=q,
        temporal_expressions=signals.temporals,
        locations=signals.locations,
    )
    lexical25_clean_query = build_lexical_text(q, signals.temporals, signals.locations)

    emb = vector_model.encode([semantic_clean_query])[0]
    semantic_vector = emb.tolist() if hasattr(emb, "tolist") else list(emb)

    return lang, lexical25_clean_query, semantic_vector, signals.temporals, signals.geo_refs


def _clean_fragment(value) -> str:
    return (str(value) or "").strip()
