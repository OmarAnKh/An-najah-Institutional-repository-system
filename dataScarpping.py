import requests
import json
import time
from pathlib import Path

# Base URL for the DSpace API
BASE_URL = "https://repository.najah.edu/server/api"

# Create output directory for data files
OUTPUT_DIR = Path("scraped_data")
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_collections():
    """
    Fetch all collections from the DSpace repository
    Handles pagination to get all collections
    Returns a list of collections with their metadata
    """
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


def save_collections_to_file(collections):
    """
    Save collections metadata to a JSON file
    """
    output_file = OUTPUT_DIR / "collections_metadata.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(collections, f, indent=2, ensure_ascii=False)

    print(f"Collections metadata saved to {output_file}")
    return output_file


def fetch_items_from_collection(collection_id, collection_name):
    """
    Fetch all items from a specific collection
    Handles pagination to get all items
    """
    print(f"\nFetching items from collection: {collection_name} (ID: {collection_id})")

    url = f"{BASE_URL}/discover/search/objects"
    params = {
        "scope": collection_id,
        "page": 0,
        "size": 100,  # Fetch 100 items per page
    }

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


def save_items_to_file(collection_id, collection_name, items):
    """
    Save items from a collection to a JSON file
    """
    # Create a safe filename from collection name
    safe_name = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in collection_name
    )
    safe_name = safe_name[:50]  # Limit filename length

    output_file = OUTPUT_DIR / f"items_{collection_id}_{safe_name}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "collection_id": collection_id,
                "collection_name": collection_name,
                "total_items": len(items),
                "items": items,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"  Items saved to {output_file}")


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

    # Step 2: Save collections metadata
    save_collections_to_file(collections)

    # Step 3: Fetch and save items from each collection
    print("\n" + "=" * 60)
    print("Fetching items from each collection...")
    print("=" * 60)

    for idx, collection in enumerate(collections, 1):
        collection_id = collection.get("id", "unknown")
        collection_name = collection.get("name", "Unnamed Collection")

        print(f"\n[{idx}/{len(collections)}] Processing: {collection_name}")

        items = fetch_items_from_collection(collection_id, collection_name)

        if items:
            save_items_to_file(collection_id, collection_name, items)
        else:
            print(f"  No items found in collection: {collection_name}")

    print("\n" + "=" * 60)
    print("Data scraping completed!")
    print(f"All data saved in: {OUTPUT_DIR.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
