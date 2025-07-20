# Scraper  

This module is responsible for scraping data from the web. It uses various libraries to fetch and parse HTML content, extract relevant information, and store it in a structured format. 

This module contains a data pipeline for collecting, processing, and storing cultural and tourism information about municipalities in Andalusia, Spain. It integrates scraping, enrichment, embedding generation, and database storage using Prefect, Selenium, Sentence Transformers, and SQLAlchemy.


## 🗂️ Project Structure

```
├─ 📁scraper
│  ├─ 📁src
│  │  ├─ helpers
│  │  │  ├─ 📄minio.py
│  │  │  ├─ 📄postgres.py
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
PGURI=postgresql+psycopg2://your_user:your_password@your_host:5432/your_database

MINIO_ROOT_USER="minioadmin"
MINIO_ROOT_PASSWORD="minioadmin"
MINIO_ENDPOINT="localhost:9000"
```

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


## 🧭 Monitoring the Pipeline
 

This project integrates **Prefect** and **MinIO** for monitoring and reporting.

### 🚦 Launch Prefect Server

To monitor flow runs, start the Prefect UI:

```bash
prefect server start
```

Open the UI in your browser:

```
http://localhost:4200
```

You can inspect:

- Registered flows and tasks
- Run status and duration
- Logs and errors

📌 *Example:*
![prefect-server](../screenshots/prefect-server.png)

---

### 📁 Access Reports in MinIO

MinIO stores JSON reports about each pipeline run.

If you're using Docker Compose, MinIO is available:

```
http://localhost:9100
```

**Login with default credentials** (if not using Docker Compose, username and password should be equal to .env)

```
Username: minioadmin
Password: minioadmin
```

Then:

1. Open the `reports`  bucket
2. Download JSON files uploaded by the `upload_report.py` task
3. Analyze task durations, results, and metadata

📌 *Example:*
![minio](../screenshots/minio.png)

---

> These reports help with auditing, debugging, and performance monitoring of scraping tasks.

---

## 📄 License

MIT – free to use, modify and distribute.



