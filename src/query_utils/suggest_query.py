def build_suggest_query(prefix: str, fetch_size: int = 60):
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
                "minimum_should_match": 1,
            }
        },
    }
