## 📚 An-Najah Institutional Repository System

A smart information-retrieval platform for An-Najah University. The system harvests repository content, enriches it with semantic metadata, and exposes search experiences such as autocomplete, geo-temporal filtering, and RAG-based question answering.

---

### 🌟 Project Overview

The stack combines traditional metadata indexing with modern vector search. Scraped collections feed an OpenSearch index that stores keyword fields, geo points, temporal expressions, and dense embeddings generated with Sentence Transformers. A retrieval layer then supports semantic search and RAG workflows.

---

### 🚀 Key Features

- Semantic search backed by dense vector embeddings.
- RAG question answering that synthesises answers from retrieved documents.
- Autocomplete powered by an edge-ngram analyzer for type-ahead suggestions.
- Spatio-temporal faceting over extracted geo and temporal metadata.
- Metadata enrichment that augments author, date, and abstract information.
- OpenSearch + FAISS + Sentence Transformers as the core search stack.

---

### ⚖️ Benefits vs. Traditional Systems

| Capability | An-Najah IR System | Legacy keyword systems |
| :--- | :--- | :--- |
| Relevance | Concept-aware retrieval with embeddings | Exact keyword matching only |
| Question answering | RAG responses from primary sources | Manual reading required |
| Search modes | Autocomplete, semantic, geo, temporal | Limited keyword filters |
| Metadata | Enriched with computed features | Raw catalog metadata only |
| Scalability | Built on modern distributed tooling | Harder to scale or extend |

---

### 🛠️ Getting Started

Follow the steps below to spin up the development environment.

#### ✅ Prerequisites

- Python 3.12 or newer
- Docker and Docker Compose
- Internet access (first run downloads the embedding model)

#### 1. Clone and create a virtual environment

```powershell
git clone https://github.com/OmarAnKh/An-najah-Institutional-repository-system.git
cd An-najah-Institutional-repository-system
python -m venv .venv
.\.venv\Scripts\activate
```

#### 2. Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure runtime settings

Create a `.env` file in the root folder (or set environment variables) with the connection details and model configuration:

```ini
EMBEDDING_MODEL_NAME=<the name of the model you want to use for embedding>
OPENSEARCH_HOST=<the host (default is locally)>
OPENSEARCH_PORT=<The port to be used>
INDEX_NAME=<the name of the index you want to create>
```

#### 4. Start OpenSearch services

If you have the provided `docker-compose.yml`, launch the stack:

```powershell
docker compose up -d
```

Wait until OpenSearch reports a healthy status before proceeding.

---

### 🧱 Architecture (N‑Layered)

The codebase follows a simple N‑layered architecture:

- **Presentation / Scripts layer**  
	- Entry points like [main.py](main.py) and the evaluation scripts under [src/evaluation](src/evaluation) (for example [src/evaluation/evaluation.py](src/evaluation/evaluation.py)).
	- Orchestrates use cases (indexing, searching, evaluation) without containing business rules or infrastructure details.

- **Application / Services layer**  
	- [src/services/an_najah_repository_search_service.py](src/services/an_najah_repository_search_service.py): wraps OpenSearch querying for the repository index.  
	- [src/services/open_seach_insertion.py](src/services/open_seach_insertion.py): application-level indexing pipeline that coordinates DTOs, extractors, and the OpenSearch client.

- **Domain layer (DTOs & extractors)**  
	- DTOs under [src/dtos](src/dtos) such as [src/dtos/article_dto.py](src/dtos/article_dto.py), [src/dtos/localized_text.py](src/dtos/localized_text.py), [src/dtos/localized_vector.py](src/dtos/localized_vector.py), [src/dtos/geo_reference.py](src/dtos/geo_reference.py), [src/dtos/geo_coordinates.py](src/dtos/geo_coordinates.py).  
	- Extractors under [src/extracters](src/extracters) for temporal and geographic information (e.g. [src/extracters/stanza_temporal_extractor.py](src/extracters/stanza_temporal_extractor.py), [src/extracters/stanza_locations_extractor.py](src/extracters/stanza_locations_extractor.py), [src/extracters/geopy_geo_location_finder.py](src/extracters/geopy_geo_location_finder.py)).

- **Infrastructure layer**  
	- OpenSearch mapping/model integration in [src/opensearch/mapping.py](src/opensearch/mapping.py).  
	- OpenSearch client + AWS IAM auth in [src/opensearch/open_search_client.py](src/opensearch/open_search_client.py).  
	- Abstract client contracts in [src/opensearch/abstract_classes](src/opensearch/abstract_classes).

This separation keeps indexing/search logic decoupled from low‑level OpenSearch and AWS configuration, and makes it easier to test or replace individual layers.

---

### 📊 Evaluation Setup

A lightweight evaluation pipeline is provided under [src/evaluation](src/evaluation) to measure search quality on a small, curated set of queries.

- **Data artifacts**  
	- [src/evaluation/export_200_docs.json](src/evaluation/export_200_docs.json): a sample of 200 documents exported from the OpenSearch index (without vectors) for offline analysis.  
	- [src/evaluation/evaluation_queries.csv](src/evaluation/evaluation_queries.csv): 15 evaluation rows. Each row contains:
		- `chunk_id`: original chunk index within a document.  
		- `abstract_ar`, `abstract_en`: the abstract text used to locate the source document.  
		- `query`: a query that is expected to retrieve that document.

- **UUID enrichment script**  
	- [src/evaluation/augment_queries_with_uuid.py](src/evaluation/augment_queries_with_uuid.py) matches each abstract in `evaluation_queries.csv` against `export_200_docs.json` and writes [src/evaluation/evaluation_queries_with_uuid.csv](src/evaluation/evaluation_queries_with_uuid.csv), adding a stable `bitstream_uuid` column.  
	- Matching strategy: normalized exact match on `abstract.en`/`abstract.ar` first, then a substring fallback.  
	- Run once (from the project root) to regenerate the enriched file:

		```bash
		python -m src.evaluation.augment_queries_with_uuid
		```

- **IR evaluation script**  
	- [src/evaluation/evaluation.py](src/evaluation/evaluation.py) runs a simple text‑based evaluation over the 15 queries.  
	- Uses `bitstream_uuid` as the **ground‑truth identifier** (document‑level), not `chunk_id`, to avoid ambiguity across chunks.  
	- For each query:
		- Builds a `multi_match` OpenSearch query over `title.en`, `title.ar`, `abstract.en`, `abstract.ar`, and `author` (with title/abstract boosted).  
		- Requests the top‑`k` hits (configurable; default `k=10`).  
		- Compares the retrieved documents’ `bitstream_uuid` values against the expected UUID.

- **Metrics**  
	All metrics are computed over the 15 queries, assuming a single relevant document per query.

	- **Accuracy@1**: fraction of queries where the top‑1 result has the expected `bitstream_uuid` (equivalent to Precision@1 here).  
	- **Recall@k (Hit@k)**: fraction of queries where the expected `bitstream_uuid` appears anywhere in the top‑`k` results.  
	- **Precision@k (macro)**: total relevant hits in the top‑`k` divided by the total number of retrieved documents up to `k` across all queries.

- **Running the evaluation**  
	With the virtual environment activated and from the project root:

	```bash
	# 1) (Optional) regenerate the enriched CSV with UUIDs
	python -m src.evaluation.augment_queries_with_uuid

	# 2) Run the evaluation using the enriched CSV
	python -m src.evaluation.evaluation
	```

	You can change `k` by editing the call at the bottom of [src/evaluation/evaluation.py](src/evaluation/evaluation.py):

	```python
	if __name__ == "__main__":
			evaluate_ir(k=10, csv_path="src/evaluation/evaluation_queries_with_uuid.csv")
	```

---

### 🧪 Next Steps

- Add more labeled queries and documents to scale evaluation beyond 15 examples.  
- Compare classical BM25 scoring against vector/knn search on the same ground‑truth set.  
- Integrate evaluation into CI (GitHub Actions) to track relevance metrics over time as the index and ranking logic evolve.
