## Demo Video

Watch the walkthrough: [Demo Video](https://example.com/your-demo-link)

---

## An-Najah Institutional Repository System

A smart information retrieval platform for An-Najah University. The system harvests repository content, enriches it with semantic metadata, and exposes search experiences such as autocomplete, geo-temporal filtering, and RAG-based question answering.

---

### Project Overview

The stack combines traditional metadata indexing with modern vector search. Scraped collections feed an OpenSearch index that stores keyword fields, geo points, temporal expressions, and dense embeddings generated with Sentence Transformers. A FastAPI service then exposes indexing, query generation, search, suggestion, and RAG answer endpoints.

---

### Key Features

- Semantic search backed by dense vector embeddings.
- RAG question answering that synthesizes answers from retrieved documents.
- Autocomplete suggestions powered by an edge-ngram analyzer.
- Spatio-temporal facets over extracted geo and temporal metadata.
- Metadata enrichment that augments author, date, and abstract information.
- OpenSearch + FAISS + Sentence Transformers as the core search stack.
- Query generation from natural language using a generative model.

---

### Benefits vs. Traditional Systems

| Capability | An-Najah IR System | Legacy keyword systems |
| :--- | :--- | :--- |
| Relevance | Concept-aware retrieval with embeddings | Exact keyword matching only |
| Question answering | RAG responses from primary sources | Manual reading required |
| Search modes | Autocomplete, semantic, geo, temporal | Limited keyword filters |
| Metadata | Enriched with computed features | Raw catalog metadata only |
| Scalability | Built on modern distributed tooling | Harder to scale or extend |

---

### Getting Started

Follow the steps below to spin up the development environment.

#### Prerequisites

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
EMBEDDING_MODEL_NAME=<Sentence-transformers model for embeddings>
OPENSEARCH_HOST=<OpenSearch host>
OPENSEARCH_PORT=<OpenSearch port>
INDEX_NAME=<OpenSearch index name>

GENERATIVE_MODEL_NAME=<Gemini model name used for query generation>
GOOGLE_API_KEY=<Google API key for Gemini>
OLLAMA_MODEL_NAME=<Optional: Ollama model name if using local LLM flows>

PIPELINE_NAME=<OpenSearch pipeline name, if applicable>
SUGGEST_URL=<OpenSearch suggest endpoint, if applicable>

# AWS credentials for OpenSearch (optional if not using AWS domain)
AWS_ACCESS_KEY_ID=<AWS access key>
AWS_SECRET_ACCESS_KEY=<AWS secret key>
AWS_REGION=<AWS region>
```

#### 4. Start OpenSearch services

If you have the provided `docker-compose.yml`, launch the stack:

```powershell
docker compose up -d
```

Wait until OpenSearch reports a healthy status before proceeding.

#### 5. Run the API server

```powershell
uvicorn main:main --host 0.0.0.0 --port 8000 --reload
```

#### 6. Run the UI (Vite/React)

The frontend lives in the `ui/` folder and talks to the same FastAPI backend via `/api/*` routes.

```powershell
cd ui
npm install
npm run dev -- --host --port 5173
```

By default Vite will proxy `/api` to the backend if served from the same host. Ensure the API server above is running. For a production build: `npm run build` (outputs to `ui/dist`).

---

### API Endpoints

All endpoints are mounted under `/api`.

- `POST /api/index` - Bulk index a JSONL file into OpenSearch.
- `POST /api/search` - Execute a custom OpenSearch query DSL body.
- `POST /api/generate-query` - Generate an OpenSearch query from a natural language prompt.
- `POST /api/answer` - Run the RAG pipeline and return an answer.
- `GET /api/suggest` - Autocomplete suggestions for a typed prefix.
- `GET /health` - Service health check.

---

### Architecture (Layered)

The codebase follows a simple layered architecture:

- **Presentation / API layer**  
  - Entry point in [main.py](main.py) and FastAPI routes under [src/api](src/api).
  - Orchestrates use cases (indexing, searching, evaluation) without containing business rules or infrastructure details.

- **Application / Services layer**  
  - [src/services/an_najah_repository_search_service.py](src/services/an_najah_repository_search_service.py): wraps OpenSearch querying, suggestions, query generation, and RAG workflows.  
  - [src/services/open_seach_insertion.py](src/services/open_seach_insertion.py): indexing pipeline that coordinates DTOs, extractors, and the OpenSearch client.

- **Domain layer (DTOs and extractors)**  
  - DTOs under [src/dtos](src/dtos) such as [src/dtos/article_dto.py](src/dtos/article_dto.py), [src/dtos/localized_text.py](src/dtos/localized_text.py), [src/dtos/localized_vector.py](src/dtos/localized_vector.py), [src/dtos/geo_reference.py](src/dtos/geo_reference.py), [src/dtos/geo_coordinates.py](src/dtos/geo_coordinates.py).  
  - Extractors under [src/extracters](src/extracters) for temporal and geographic information (e.g. [src/extracters/stanza_temporal_extractor.py](src/extracters/stanza_temporal_extractor.py), [src/extracters/stanza_locations_extractor.py](src/extracters/stanza_locations_extractor.py), [src/extracters/geopy_geo_location_finder.py](src/extracters/geopy_geo_location_finder.py)).

- **Infrastructure layer**  
  - OpenSearch mapping/model integration in [src/opensearch/mapping.py](src/opensearch/mapping.py).  
  - OpenSearch client + AWS IAM auth in [src/opensearch/open_search_client.py](src/opensearch/open_search_client.py).  
  - Abstract client contracts in [src/opensearch/abstract_classes](src/opensearch/abstract_classes).

This separation keeps indexing/search logic decoupled from low-level OpenSearch and AWS configuration, and makes it easier to test or replace individual layers.

---

### Evaluation Setup

A lightweight evaluation pipeline is provided under [src/evaluation](src/evaluation) to measure search quality on a small, curated set of queries.

- **IR evaluation script**  
  - [src/evaluation/evaluation.py](src/evaluation/evaluation.py) runs a simple text-based evaluation over the 15 queries.  
  - Uses `bitstream_uuid` as the ground-truth identifier (document-level), not `chunk_id`, to avoid ambiguity across chunks.  
  - For each query:
    - Builds a `multi_match` OpenSearch query over `title.en`, `title.ar`, `abstract.en`, `abstract.ar`, and `author` (with title/abstract boosted).  
    - Requests the top `k` hits (configurable; default `k=10`).  
    - Compares the retrieved documents' `bitstream_uuid` values against the expected UUID.

- **Metrics**  
  All metrics are computed over the 15 queries, assuming a single relevant document per query.

  - **Accuracy@1**: fraction of queries where the top 1 result has the expected `bitstream_uuid` (equivalent to Precision@1 here).  
  - **Recall@k (Hit@k)**: fraction of queries where the expected `bitstream_uuid` appears anywhere in the top `k` results.  
  - **Precision@k (macro)**: total relevant hits in the top `k` divided by the total number of retrieved documents up to `k` across all queries.

- **Running the evaluation**  
  With the virtual environment activated and from the project root:

  ```bash
  python -m src.evaluation.evaluation
  ```

  You can change `k` by editing the call at the bottom of [src/evaluation/evaluation.py](src/evaluation/evaluation.py):

  ```python
  if __name__ == "__main__":
      evaluate_ir(k=10, csv_path="src/evaluation/evaluation_queries_with_uuid.csv")
  ```

---
