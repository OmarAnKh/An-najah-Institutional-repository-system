import requests
import json
import time
from pathlib import Path

BASE_URL = "https://repository.najah.edu/server/api"

OUTPUT_DIR = Path("scraped_data")
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_collections():
    print("Fetching collections...")
    url = f"{BASE_URL}/core/collections"

    all_collections = []
    page = 0

    while True:
        params = {"page": page, "size": 100}  # Fetch 100 collections per page

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "_embedded" in data and "collections" in data["_embedded"]:
                collections = data["_embedded"]["collections"]
                all_collections.extend(collections)
                print(f"  Page {page + 1}: Retrieved {len(collections)} collections")

                # Check if there are more pages
                page_info = data.get("page", {})
                total_pages = page_info.get("totalPages", 1)
                total_elements = page_info.get("totalElements", 0)

                if page == 0:
                    print(f"  Total collections available: {total_elements}")

                if page + 1 >= total_pages:
                    break

                page += 1
                time.sleep(0.5)  # Be nice to the API
            else:
                print("No collections found in the response")
                break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching collections: {e}")
            break

    print(f"Total collections retrieved: {len(all_collections)}")
    return all_collections


def fetch_items_from_collection(collection_id, collection_name):
    print(f"\nFetching items from collection: {collection_name} (ID: {collection_id})")

    url = f"{BASE_URL}/discover/search/objects"
    params = {"scope": collection_id, "page": 0, "size": 100}

    all_items = []
    page = 0

    while True:
        params["page"] = page

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract items from the response
            if "_embedded" in data and "searchResult" in data["_embedded"]:
                search_result = data["_embedded"]["searchResult"]

                if (
                    "_embedded" in search_result
                    and "objects" in search_result["_embedded"]
                ):
                    items = search_result["_embedded"]["objects"]
                    all_items.extend(items)
                    print(f"  Page {page + 1}: Retrieved {len(items)} items")

                    # Check if there are more pages
                    page_info = data.get("page", {})
                    total_pages = page_info.get("totalPages", 1)

                    if page + 1 >= total_pages:
                        break

                    page += 1
                    time.sleep(0.5)  # Be nice to the API
                else:
                    break
            else:
                break

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching items from collection {collection_id}: {e}")
            break

    print(f"  Total items retrieved: {len(all_items)}")
    return all_items


def fetch_item_metadata(item_uuid):
    url = f"{BASE_URL}/core/items/{item_uuid}/bundles"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching bundles for item {item_uuid}: {e}")
        return None


def fetch_bundle_item(bundle_id):
    if not bundle_id:
        return None

    url = f"{BASE_URL}/core/bundles/{bundle_id}/item"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching item for bundle {bundle_id}: {e}")
        return None


def fetch_bundle_bitstreams(bundle_id):
    if not bundle_id:
        return []

    url = f"{BASE_URL}/core/bundles/{bundle_id}/bitstreams"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data.get("_embedded", {}).get("bitstreams", [])
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching bitstreams for bundle {bundle_id}: {e}")
        return []


def build_document_from_item(collection, item_obj):
    # discover/search result wraps the real item under _embedded.indexableObject
    item = item_obj.get("_embedded", {}).get("indexableObject", {})
    item_uuid = item.get("id")
    collection_name = collection.get("name", "")

    # metadata is usually under "metadata" for core item responses
    # but here we come from discover/search, so we will re-fetch via bundles->item
    bundles = fetch_item_metadata(item_uuid) or {}
    bundles_list = bundles.get("_embedded", {}).get("bundles", [])

    # Find ORIGINAL bundle and get its first bitstream UUID via /bitstreams
    bitstream_uuid = None
    for b in bundles_list:
        if b.get("type") == "bundle" and b.get("name") == "ORIGINAL":
            original_id = b.get("uuid") or b.get("id")
            for bs in fetch_bundle_bitstreams(original_id):
                bitstream_uuid = bs.get("uuid") or bs.get("id")
                if bitstream_uuid:
                    break
            break

    # Call bundles/{id}/item to get full item metadata (title, authors, abstract, etc.)
    full_item = None
    if bundles_list:
        first_bundle_id = bundles_list[0].get("uuid") or bundles_list[0].get("id")
        if first_bundle_id is not None:
            full_item = fetch_bundle_item(first_bundle_id) or {}

    # Prefer metadata from the full item; if unavailable, fall back to indexableObject
    metadata = (full_item or {}).get("metadata") or item.get("metadata", {})

    def all_lang_values(key):
        out = {"en": [], "ar": []}
        for v in metadata.get(key, []):
            lang = (v.get("language") or "").lower()
            val = v.get("value") or ""
            if not val:
                continue
            if lang.startswith("ar"):
                out["ar"].append(val)
            else:
                out["en"].append(val)
        return out

    def first_value(key):
        values = metadata.get(key) or []
        if values:
            return values[0].get("value")
        return None

    titles = all_lang_values("dc.title")
    abstracts = all_lang_values("dc.description.abstract")

    # authors as array of strings
    authors = [v.get("value") for v in metadata.get("dc.contributor.author", [])]

    publication_date = first_value("dc.date.issued") or None

    doc = {
        "collection": collection_name,
        "bitstream_uuid": bitstream_uuid,
        "chunk_id": None,
        "title": {
            "en": titles["en"],
            "ar": titles["ar"],
        },
        "author": authors,
        "abstract": {
            "en": abstracts["en"],
            "ar": abstracts["ar"],
        },
        "hasFiles": bool(bitstream_uuid),
        "publicationDate": publication_date,
        "reportLocation": None,
        "geoReferences": [],
        "temporalExpressions": [],
    }

    return item_uuid, doc


def main():
    """
    Main function to orchestrate the data scraping process
    """
    print("=" * 60)
    print("DSpace Repository Data Scraper")
    print("=" * 60)

    # Step 1: Fetch all collections
    collections = fetch_collections()

    if not collections:
        print("No collections to process. Exiting.")
        return

    print("\n" + "=" * 60)
    print("Fetching items from each collection and building bulk documents...")
    print("=" * 60)

    bulk_path = OUTPUT_DIR / "bulk_opensearch.jsonl"
    with open(bulk_path, "w", encoding="utf-8") as f:
        for idx, collection in enumerate(collections, 1):
            collection_id = collection.get("id", "unknown")
            collection_name = collection.get("name", "Unnamed Collection")

            print(f"\n[{idx}/{len(collections)}] Processing: {collection_name}")

            items = fetch_items_from_collection(collection_id, collection_name)

            for item in items:
                item_uuid, doc = build_document_from_item(collection, item)
                if not item_uuid:
                    continue
                # Write each document as a standalone JSON line (no bulk header)
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print("\n" + "=" * 60)
    print("Document JSONL generation completed!")
    print(f"File written to: {bulk_path.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
