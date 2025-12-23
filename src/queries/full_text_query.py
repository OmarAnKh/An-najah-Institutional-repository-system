"""Hybrid OpenSearch query builder used for full-text retrieval."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.queries.query_preprocessor import expand_year_ranges, filter_safe_temporals

DEFAULT_EXCLUDES = ["abstract_vector.en", "abstract_vector.ar"]


def _wrap_with_filters(
    q: Dict[str, Any],
    filters: List[Dict[str, Any]],
    should_boosts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Attach optional filters/boosts to a leaf query."""

    should_boosts = should_boosts or []
    if not filters and not should_boosts:
        return q

    out: Dict[str, Any] = {"bool": {"must": [q]}}
    if filters:
        out["bool"]["filter"] = filters
    if should_boosts:
        out["bool"]["should"] = should_boosts
        out["bool"]["minimum_should_match"] = 0
    return out


def _temporal_boosts(temporal_expressions: Optional[List[str]]) -> List[Dict[str, Any]]:
    safe_years = expand_year_ranges(filter_safe_temporals(temporal_expressions))
    if not safe_years:
        return []

    return [
        {
            "constant_score": {
                "filter": {"terms": {"temporalExpressions": safe_years}},
                "boost": 0.6,
            }
        }
    ]


def _geo_boosts(
    geo_refs: Optional[List[Dict[str, Any]]], geo_distance_str: str
) -> List[Dict[str, Any]]:
    if not geo_refs:
        return []

    place_boosts: List[Dict[str, Any]] = []
    distance_filters: List[Dict[str, Any]] = []
    seen_places = set()

    for ref in geo_refs:
        place_name = (ref.get("placeName") or "").strip()
        lat = ref.get("lat")
        lon = ref.get("lon")

        if place_name:
            place_key = place_name.lower()
            if place_key not in seen_places:
                seen_places.add(place_key)
                place_boosts.append(
                    {
                        "nested": {
                            "path": "geoReferences",
                            "query": {
                                "match": {
                                    "geoReferences.placeName": {
                                        "query": place_name,
                                        "boost": 5.0,
                                    }
                                }
                            },
                        }
                    }
                )

        if lat is not None and lon is not None:
            distance_filters.append(
                {
                    "geo_distance": {
                        "distance": geo_distance_str,
                        "geoReferences.coordinates": {
                            "lat": float(lat),
                            "lon": float(lon),
                        },
                    }
                }
            )

    boosts: List[Dict[str, Any]] = []
    if distance_filters:
        boosts.append(
            {
                "constant_score": {
                    "filter": {
                        "nested": {
                            "path": "geoReferences",
                            "query": {
                                "bool": {
                                    "should": distance_filters,
                                    "minimum_should_match": 0,
                                }
                            },
                        }
                    },
                    "boost": 2.0,
                }
            }
        )

    boosts.extend(place_boosts)
    return boosts


def build_hybrid_query_pipeline(
    lexical25_text: str,
    semantic_query_vector: List[float],
    temporal_expressions: Optional[List[str]] = None,
    geo_refs: Optional[List[Dict[str, Any]]] = None,
    size: int = 10,
    k: int = 50,
    num_candidates: Optional[int] = 100,
    geo_distance_str: str = "50km",
    lang: str = "en",
    collapse_field: Optional[str] = "bitstream_uuid",
) -> Dict[str, Any]:
    """Build a concise hybrid query (BM25 + kNN) with soft boosts.

    The resulting DSL keeps results deduplicated (via collapse) and
    reuses a single list of boosts across the lexical and semantic legs.
    """

    vector_field = f"abstract_vector.{lang}"
    title_text_field = f"title.{lang}"
    abstract_text_field = f"abstract.{lang}"

    filters: List[Dict[str, Any]] = []
    should_boosts = _temporal_boosts(temporal_expressions)
    should_boosts.extend(_geo_boosts(geo_refs, geo_distance_str))

    hybrid_query = {
        "hybrid": {
            "queries": [
                _wrap_with_filters(
                    {
                        "knn": {
                            vector_field: {
                                "vector": semantic_query_vector,
                                "k": k,
                                "method_parameters": {
                                    "ef_search": int(num_candidates or 100)
                                },
                            }
                        }
                    },
                    filters,
                    should_boosts,
                ),
                _wrap_with_filters(
                    {
                        "multi_match": {
                            "query": lexical25_text,
                            "fields": [
                                f"{title_text_field}^3",
                                f"{abstract_text_field}^2",
                            ],
                            "type": "best_fields",
                            "minimum_should_match": "60%",
                        }
                    },
                    filters,
                    should_boosts,
                ),
            ]
        }
    }

    body: Dict[str, Any] = {
        "size": size,
        "_source": {"excludes": DEFAULT_EXCLUDES},
        "query": hybrid_query,
        "track_total_hits": True,
    }

    if collapse_field:
        body["collapse"] = {"field": collapse_field}

    return body
