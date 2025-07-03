# Scraper  

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-FF4F00?style=for-the-badge&logo=MinIO&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4B0082?style=for-the-badge)
![SentenceTransformers](https://img.shields.io/badge/SentenceTransformer-FFCC00?style=for-the-badge)


This module is responsible for scraping data from the web. It uses various libraries to fetch and parse HTML content, extract relevant information, and store it in a structured format. 

This module contains a data pipeline for collecting, processing, and storing cultural and tourism information about municipalities in Andalusia, Spain. It integrates scraping, enrichment, embedding generation, and database storage using Prefect, Selenium, Sentence Transformers, and SQLAlchemy.



## 🚀 Main Technologies Used

- **Python 3.12**: Main programming language.
- **Prefect**: Orchestrates and schedules scraping and data-processing tasks.
- **PostgreSQL**: Stores structured data and embeddings.
- **MinIO**: Object storage compatible with Amazon S3, used for storing tasks reports.
- **Selenium**: Automates interactions with dynamic websites.
- **BeautifulSoup**: Parses and extracts data from static HTML.
- **SentenceTransformer**: Generates semantic embeddings for similarity comparison.
- **SQLAlchemy**: ORM for interacting with PostgreSQL.

## 🗂️ Project Structure

```
├─ 📁scraper
│  ├─ 📁src
│  │  ├─ 📁config
│  │  │  ├─ 📄minio.py
│  │  │  └─ 📄selenium.py
│  │  ├─ 📁models
│  │  │  └─ 📄municipality.py
│  │  ├─ 📁pipeline
│  │  │  ├─ 📄main.py
│  │  │  └─ 📄__init__.py
│  │  └─ 📁tasks
│  │     ├─ 📄generate_embeddings.py
│  │     ├─ 📄get_andalusia_towns_ubi_and_name.py
│  │     ├─ 📄get_info_from_iaph.py
│  │     ├─ 📄get_towns_descriptions.py
│  │     ├─ 📄merge_munipacilty_info.py
│  │     ├─ 📄save_data.py
│  │     ├─ 📄scrape_from_turismo_andalucia.py
│  │     ├─ 📄upload_report.py
│  │     ├─ 📄wikipedia_beach_check.py
│  │     └─ 📄__init__.py
│  ├─ 📄.env-template
│  ├─ 📄.python-version
│  ├─ 📄Dockerfile
│  ├─ 📄pyproject.toml
│  ├─ 📄README.md
│  ├─ 📄requirements.txt
│  └─ 📄uv.lock
```


## ⚙️ How to Use

> ⚠️ Make sure Python 3.12 is installed. PostgreSQL and MinIO must be running locally or in Docker.

### 🔸 Using [`uv`](https://github.com/astral-sh/uv)

```bash
uv pip install -e ../utils-project
uv pip install -e .
uv run src/pipeline/main.py
```

### 🔹 Using `pip`

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -e ../utils-project
pip install -e .
python src/pipeline/main.py
```

### 🌍 Configure environment

Rename `.env-template` to `.env` and customize if needed:

```env
POSTGRES_DB="scraper"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="mysecretpassword"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"

MINIO_ROOT_USER="minioadmin"
MINIO_ROOT_PASSWORD="minioadmin"
MINIO_HOST="localhost"
MINIO_PORT="9000"
```

---






## 🧪 Main Scripts Overview
### `src/pipeline/main.py`
Coordinates the overall pipeline execution. 
1. **Fetch town data** from the Junta de Andalucía API.
2. **Scrape tourism content** (description, history, images) from [andalucia.org](https://andalucia.org).
3. In parallel:
   - Fetch **towns with beaches** from Wikipedia.
   - Retrieve **cultural assets** (real estate and intangible) from IAPH.
4. **Merge all data** into unified municipality records.
5. **Generate embeddings** using Sentence Transformers.
6. **Load data into PostgreSQL**, including towns, cultural assets, and images.
7. **Upload a metadata report** of the run to MinIO.

Tasks are composed using Prefect's `@flow` and `@task` decorators and executed concurrently where possible for efficiency.

![prefect-server](../screenshots/prefect-server.png)

### 📄Tasks

### `get_andalusia_towns_ubi_and_name.py`
**Purpose:**  
Fetches a list of municipalities in Andalusia (including coordinates and province info) from the Junta de Andalucía API.

**Highlights:**
- Filters only towns in recognized provinces using `province_identifier`.
- Outputs a structured list with location and administrative data for each town.

---
### `scrape_from_turismo_andalucia.py`
**Purpose:**  
Scrapes tourism data (description, history, images) for municipalities in Andalusia from the official [andalucia.org](https://andalucia.org) website.

**Highlights:**
- Uses Selenium for dynamic web scraping.
- Accepts cookies, extracts text before/after specific headers (`<h2>`), and gathers image URLs.
- Supports multithreading with `ThreadPoolExecutor` for performance.
- Returns enriched town data with tourism content.

---

### `wikipedia_beach_check.py`
**Purpose:**  
Identifies Andalusian municipalities with beaches by scraping a Wikipedia page.

**Highlights:**
- Scrapes [`Anexo:Playas_de_Andalucía`](https://es.wikipedia.org/wiki/Anexo:Playas_de_Andaluc%C3%ADa) using `requests` and `BeautifulSoup`.
- Filters towns by valid Andalusian provinces.
- Outputs a list of towns with coastal beaches.

---


### `get_info_from_iaph.py`
**Purpose:**  
Retrieves detailed data on cultural assets (real estate and intangible) from the IAPH (Instituto Andaluz del Patrimonio Histórico).

**Highlights:**
- Supports async fetching via `httpx` for high concurrency.
- Cleans and standardizes asset metadata into Pydantic models.
- Handles both real estate (`inmueble`) and intangible (`inmaterial`) assets.
- Returns processed data as `polars` DataFrames.

---

### `merge_munipacilty_info.py`
**Purpose:**  
Merges multiple data sources (beach info, tourism content, cultural assets) into a unified data model per municipality.

**Highlights:**
- Normalizes names to ensure accurate data merging.
- Groups cultural assets by town.
- Constructs `MunicipalityInfo` objects for each location.

---
### `generate_embeddings.py`
**Purpose:**  
Generates sentence embeddings for municipalities and maps them to database objects for towns, intangible assets, real estate, and images.

**Highlights:**
- Uses `SentenceTransformer` (MiniLM model).
- Converts text content to vector embeddings.
- Constructs SQLAlchemy-compatible data models for downstream insertion.
- Handles batch processing with logging and error handling.

---
### `save_data.py`
**Purpose:**  
Saves structured municipality data into a PostgreSQL database with upsert logic.

**Highlights:**
- Handles towns, images, intangible assets, and real estate records.
- Deduplicates entries based on keys (e.g. `municipality_ine`, `name`).
- Uses efficient batch processing and safe transaction handling with rollback support.

![table-results](../screenshots/postgres.png)
---
### `upload_report.py`
**Purpose:**  
Extracts task metadata from Prefect task runs and uploads a report to MinIO in JSON format.

**Highlights:**
- Uses Prefect’s orchestration API to query metadata about task runs.
- Serializes datetime and UUID objects safely to JSON.
- Organizes metadata into structured records and uploads it to a versioned object path in MinIO.

![alt text](../screenshots/minio.png)

## 🧠 Why Use Embeddings?

Embeddings convert apartment descriptions into **numerical vectors** that capture semantic meaning. This enables **search by similarity** (e.g., "Find apartments like this one") using metrics like **cosine similarity**.

You can query similar listings directly from the database using vector extensions such as [pgvector](https://github.com/pgvector/pgvector) or [PGEmbedding](https://python.langchain.com/docs/integrations/vectorstores/pgembedding/), or export them to a vector database like Qdrant, Pinecone, or FAISS.

This transforms your scraped data into a **semantic search engine** for real estate listings.



## 📄 License

MIT – free to use, modify and distribute.



