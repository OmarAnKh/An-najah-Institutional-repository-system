def build_suggest_query(prefix: str, fetch_size: int = 60):
    """
    Build an OpenSearch query body for autocomplete suggestions.

    The query is optimized for interactive typeahead:
    - Primary clause: `multi_match` with `phrase_prefix` for strong prefix matches.
    - Fallback clause: fuzzy `multi_match` to tolerate typos.
    - Uses `minimum_should_match=1` so at least one clause must match.
    - Limits response `_source` to suggestion-bearing fields (title, author).

    Args:
        prefix: The user-typed query prefix.
        fetch_size: Number of candidate hits to retrieve before post-processing.

    Returns:
        A dictionary representing the OpenSearch query body.
    """
    prefix = (prefix or "").strip()

    return {
        "size": fetch_size,
        "track_total_hits": False,
        "terminate_after": 2000,
        "_source": ["title", "author"],
        "query": {
            "bool": {
                "should": [
                    # 1) Autocomplete (prefix) - ranks highest
                    {
                        "multi_match": {
                            "query": prefix,
                            "type": "phrase_prefix",
                            "fields": [
                                "title.en^4",
                                "title.ar^4",
                                "author^2",
                            ],
                            "boost": 3.0,
                        }
                    },
                    # 2) Fuzzy fallback (typos) - ranks lower than clean prefix matches
                    {
                        "multi_match": {
                            "query": prefix,
                            "fields": [
                                "title.en^4",
                                "title.ar^4",
                                "author^2",
                            ],
                            "operator": "and",
                            "fuzziness": "AUTO",
                            "prefix_length": 2,
                            "max_expansions": 50,
                        }
                    },
                ],
            }
        },
    }
