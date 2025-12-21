from typing import Any, Dict, List, Optional

from src.query_utils.query_preprocessor import filter_safe_temporals, expand_year_ranges


def _wrap_with_filters(
    q: Dict[str, Any],
    filters: List[Dict[str, Any]],
    should_boosts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Wrap a leaf query with optional hard filters and soft boosts.

    This helper keeps lexical and semantic queries consistent by applying:
    - `filter`: hard constraints (must match; does not affect score).
    - `should`: soft preferences (boosts score when matched).

    If no filters/boosts are provided, the input query is returned unchanged.

    Args:
        q: A leaf OpenSearch query (e.g., knn, multi_match).
        filters: Hard filter clauses applied under `bool.filter`.
        should_boosts: Optional boosting clauses applied under `bool.should`.

    Returns:
        A query dictionary, possibly wrapped in a `bool` query.
    """
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
) -> Dict[str, Any]:
    """
    Build a hybrid OpenSearch query body (BM25 + kNN) with soft temporal/geo boosts.

    The pipeline combines two retrieval signals:
    1) Semantic retrieval using kNN over `abstract_vector.<lang>`.
    2) Lexical retrieval using BM25 (`multi_match`) over title/abstract fields.

    Extracted signals from preprocessing are incorporated as *soft boosts*:
    - Temporal expressions are expanded into year tokens and boosted via
      `constant_score` on `temporalExpressions` (not hard-filtered).
    - Geographic references are boosted by:
        - Matching place names in nested `geoReferences.placeName`.
        - Boosting documents within `geo_distance_str` when coordinates exist.

    Args:
        lexical25_text: Cleaned lexical query text for BM25 matching.
        semantic_query_vector: Embedding vector used for kNN retrieval.
        temporal_expressions: Optional extracted temporal expressions (e.g., years/ranges).
        geo_refs: Optional geo references (dicts with placeName + coordinates/lat-lon).
        size: Number of hits to return.
        k: Number of nearest neighbors for the kNN query.
        num_candidates: Candidate pool size (ef_search) for kNN retrieval.
        geo_distance_str: Distance radius for geo boosting (e.g., "50km").
        lang: Language selector ("en" or "ar") used to pick the correct fields.

    Returns:
        An OpenSearch query body dictionary for hybrid retrieval.
    """

    temporal_expressions = temporal_expressions or []
    if isinstance(temporal_expressions, set):
        temporal_expressions = sorted(temporal_expressions)

    geo_refs = geo_refs or []

    vector_field = f"abstract_vector.{lang}"
    title_text_field = f"title.{lang}"
    abstract_text_field = f"abstract.{lang}"

    # --------- FILTERS ----------
    filters: List[Dict[str, Any]] = []
    should_boosts: List[Dict[str, Any]] = []
    geo_place_should: List[Dict[str, Any]] = []

    # Soft temporal preference:
    # Keep years/ranges as BOOSTS (not filters), because extractor/index tokens can mismatch.
    safe = expand_year_ranges(filter_safe_temporals(temporal_expressions))
    if safe:
        should_boosts.append(
            {
                "constant_score": {
                    "filter": {"terms": {"temporalExpressions": safe}},
                    "boost": 0.6,  # gentle bonus; avoids year tokens hijacking ranking
                }
            }
        )

    # Soft geo preference:
    # 1) match place names (nested match)
    # 2) boost by distance when coordinates exist
    geo_place_should: List[Dict[str, Any]] = []
    if geo_refs:
        nested_distance_should: List[Dict[str, Any]] = []

        for ref in geo_refs:
            place_name = (ref.get("placeName") or "").strip()
            lat = ref.get("lat")
            lon = ref.get("lon")

            if lat is None or lon is None:
                coords = ref.get("coordinates") or {}
                lat = coords.get("lat")
                lon = coords.get("lon")

            if place_name:
                geo_place_should.append(
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
                nested_distance_should.append(
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

        if nested_distance_should:
            should_boosts.append(
                {
                    "constant_score": {
                        "filter": {
                            "nested": {
                                "path": "geoReferences",
                                "query": {
                                    "bool": {
                                        "should": nested_distance_should,
                                        "minimum_should_match": 0,
                                    }
                                },
                            }
                        },
                        "boost": 2.0,
                    }
                }
            )

        if geo_place_should:
            # Add place-name matches as soft boosts too
            should_boosts.extend(geo_place_should)

    # --------- HYBRID QUERY (for pipeline normalization) ----------
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
                                    "ef_search": (
                                        int(num_candidates)
                                        if num_candidates is not None
                                        else 100
                                    )
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
    # geo_place_should already included as soft boosts (should_boosts)

    body: Dict[str, Any] = {
        "size": size,
        "_source": {"excludes": ["abstract_vector.en", "abstract_vector.ar"]},
        "query": hybrid_query,
    }

    return body
