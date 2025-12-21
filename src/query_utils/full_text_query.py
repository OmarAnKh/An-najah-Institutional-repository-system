from typing import Any, Dict, List, Optional

from src.query_utils.query_preprocessor import filter_safe_temporals, expand_year_ranges

def _wrap_with_filters(
    q: Dict[str, Any],
    filters: List[Dict[str, Any]],
    should_boosts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Wrap a leaf query with:
      - filter: HARD constraints (must match)
      - should: SOFT preferences (boost only)
    This keeps semantic (kNN) and lexical queries consistent.
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
                    filters, should_boosts,
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
                            "minimum_should_match": "60%"
                        }
                    },
                    filters, should_boosts,
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
