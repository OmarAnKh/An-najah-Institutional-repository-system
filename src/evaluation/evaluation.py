import csv
from dataclasses import dataclass
from typing import Dict, List, Tuple

from global_config import global_config
from src.opensearch.open_search_client import OpenSearchClient
from src.services.an_najah_repository_search_service import (
    AnNajahRepositorySearchService,
)


@dataclass
class QueryExample:
    """Single evaluation example loaded from evaluation_queries.csv."""

    bitstream_uuid: str
    chunk_id: str
    abstract_ar: str
    abstract_en: str
    query: str


def load_queries(csv_path: str) -> List[QueryExample]:
    """Load evaluation queries from a CSV file.

    Expected header: bitstream_uuid, chunk_id, abstract_ar, abstract_en, query
    Args:
        csv_path (str): The path to the CSV file.
    Returns:
        List[QueryExample]: List of loaded query examples.
    """

    examples: List[QueryExample] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue

            bitstream_uuid = (row.get("bitstream_uuid") or "").strip()
            chunk_id = (row.get("chunk_id") or "").strip()
            query = (row.get("query") or "").strip()

            # Skip entries without a query text
            if not query:
                continue

            # Skip rows without a UUID (should be rare if augmentation worked)
            if not bitstream_uuid:
                continue

            examples.append(
                QueryExample(
                    bitstream_uuid=bitstream_uuid,
                    chunk_id=chunk_id,
                    abstract_ar=(row.get("abstract_ar") or "").strip(),
                    abstract_en=(row.get("abstract_en") or "").strip(),
                    query=query,
                )
            )

    return examples


def build_search_body(query_text: str, size: int) -> Dict:
    """Build a simple multi_match query over title and abstract.

    This intentionally keeps things simple: we just search in Arabic/English
    title and abstract fields with a bit of boosting on titles.
    """

    return {
        "size": size,
        "query": {
            "multi_match": {
                "query": query_text,
                "fields": [
                    "title.en^3",
                    "title.ar^3",
                    "abstract.en^2",
                    "abstract.ar^2",
                    "author",
                ],
                "type": "best_fields",
            }
        },
    }


def evaluate_ir(*, k: int = 10, csv_path: str) -> Tuple[float, float, float]:
    """Run a simple IR evaluation over the queries in ``csv_path``.

    Metrics (all in [0, 1]):
    - accuracy@1    : fraction of queries where the top-1 hit has the expected UUID
    - recall@k      : fraction of queries where any of the top-k hits has the
                      expected UUID (Hit@K)
    - precision@k   : macro Precision@k over all queries, i.e.
                      (total relevant hits in top-k) / (total retrieved up to k)
    """

    examples = load_queries(csv_path)
    if not examples:
        raise RuntimeError(f"No evaluation queries found in {csv_path}")

    # Initialize OpenSearch-backed search service
    client = OpenSearchClient(use_ssl=True, verify_certs=True)
    search_service = AnNajahRepositorySearchService(
        index=global_config.index_name,
        client=client,
    )

    total = len(examples)
    correct_top1 = 0
    correct_topk = 0
    total_retrieved = (
        0  # number of documents retrieved across all queries (<= total * k)
    )

    print(f"Loaded {total} evaluation queries from {csv_path}")
    print(f"Evaluating against index '{global_config.index_name}' with k={k}\n")

    for idx, ex in enumerate(examples, start=1):
        expected_uuid = (ex.bitstream_uuid or "").strip()
        search_body = build_search_body(ex.query, size=k)

        try:
            response = search_service.search_articles(search_body)
            response = search_service.user_query(search_body)
        except Exception as e:
            print(f"[ERROR] Query {idx} failed: {e}")
            continue

        hits = (response or {}).get("hits", {}).get("hits", [])
        retrieved_uuids: List[str] = []

        for h in hits:
            source = h.get("_source") or {}
            uuid_val = source.get("bitstream_uuid")
            if uuid_val is None:
                continue
            retrieved_uuids.append(str(uuid_val).strip())

        # Count how many results we actually retrieved for this query (<= k)
        total_retrieved += len(retrieved_uuids)

        top1_uuid = retrieved_uuids[0] if retrieved_uuids else None
        hit_at_1 = (
            top1_uuid is not None and expected_uuid != "" and top1_uuid == expected_uuid
        )
        hit_at_k = expected_uuid != "" and expected_uuid in retrieved_uuids

        if hit_at_1:
            correct_top1 += 1
        if hit_at_k:
            correct_topk += 1

        print(
            f"Query {idx:02d}: expected_uuid={expected_uuid!r}, "
            f"top1_uuid={top1_uuid!r}, hit@1={hit_at_1}, hit@{k}={hit_at_k}"
        )

    accuracy_at_1 = correct_top1 / total if total else 0.0
    recall_at_k = correct_topk / total if total else 0.0
    precision_at_k = (correct_topk / total_retrieved) if total_retrieved > 0 else 0.0

    print("\n=== Summary ===")
    print(f"Total queries        : {total}")
    print(f"Accuracy@1           : {accuracy_at_1:.3f}")
    print(f"Recall@{k:<2d} (Hit@{k})   : {recall_at_k:.3f}")
    print(f"Precision@{k:<2d} (macro) : {precision_at_k:.3f}")

    return accuracy_at_1, recall_at_k, precision_at_k


if __name__ == "__main__":
    evaluate_ir(k=10, csv_path="src/evaluation/evaluation_queries_with_uuid.csv")
