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
cd An-najah-Institutional-repository-system\university\IR\porject
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
EMBEDDING_MODEL_NAME="the name of the model you want to use for embedding"
OPENSEARCH_HOST="the host (default is locally)"
OPENSEARCH_PORT="The port to be used"
INDEX_NAME="the name of the index you want to create"
```

#### 4. Start OpenSearch services

If you have the provided `docker-compose.yml`, launch the stack:

```powershell
docker compose up -d
```

Wait until OpenSearch reports a healthy status before proceeding.

---

### 🧪 Next Steps

- Add automation to transform scraped JSON into index-ready documents.
- Extend the mapping and analyzers as new search facets are required.
- Integrate an application layer (API/UI) that consumes the search endpoints and RAG pipeline.