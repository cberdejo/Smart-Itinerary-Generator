# Backend

A FastAPI-based microservice that generates personalized travel itineraries using semantic similarity, real driving times, and cultural asset data from Andalusian towns.

---

## 🚀 Technologies Used

- **FastAPI** — High-performance web framework for building APIs
- **Uvicorn** — Lightning-fast ASGI server
- **SQLAlchemy Async** — Asynchronous ORM for PostgreSQL
- **Valhalla** — Open-source routing engine (based on OpenStreetMap)
- **scikit-learn** — Used for semantic similarity (cosine distance)
- **Pydantic** — Data validation and serialization
- **Docker + uv.lock** — Reproducible and isolated environment

---

## 📁 Project Structure

```
backend
├─ 📁src
│  ├─ 📁api
│  │  ├─ 📁controllers
│  │  │  └─ 📄get_itinerary.py
│  │  ├─ 📄app.py
│  │  ├─ 📄dependencies.py
│  │  ├─ 📄main.py
│  │  ├─ 📄routes.py
│  ├─ 📁backend.egg-info
│  ├─ 📁helpers
│  │  ├─ 📄postgres.py
│  │  └─ 📄valhalla.py
│  └─ 📁models
│     ├─ 📄form_response.py
│     ├─ 📄generic_response.py
│     ├─ 📄itinerary.py
│     ├─ 📄municiaplity.py
│     ├─ 📄valhalla.py
├─ 📄.env-template
├─ 📄.python-version
├─ 📄Dockerfile
├─ 📄pyproject.toml
├─ 📄README.md
└─ 📄uv.lock

```

## ⚙️ Environment Variables (`.env`)

Before running, create a `.env` file with the following:

```env
# API Host and Port
HOST=0.0.0.0
PORT=8000

# Valhalla routing service
VALHALLA_URL=http://valhalla:8002

# PostgreSQL database credentials
PGURI=postgresql+psycopg2://your_user:your_password@your_host:5432/your_database

```


## 📦 Running with Docker

Run the dockerfile with:

```bash
docker build -t smart-itinerary-api .
docker run -p 8000:8000 smart-itinerary-api
```


##  🧰 Manual Installation (Without Docker)
### 🔸 Using [`uv`](https://github.com/astral-sh/uv)

```bash
uv pip install -e ../utils-project
uv pip install -e .
uv run src/api/main.py
```

### 🔹 Using `pip`

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -e ../utils-project
pip install -e .
python src/pipeline/main.py
```
## Notes 
- ⚠️ Make sure to have a Valhalla instance running.
- You can try the endpoints with `curl`, `postman` or with [frontend module](/frontend/) (recommended) 


## 🔌 Main API Endpoints

You can check the docs in `host`:`port`/docs

![alt text](../screenshots/swagger.png)

### `GET /api/v1/health`
Check if the api and database are active

### `POST /api/v1/itinerary`

🧠 Generate a tailored travel itinerary based on user preferences.



## 🔍 Key Features

- 🏖️ **Town filtering**: beach preference, proximity via isochrones
- 🧠 **Semantic recommendations**: embedding-based ranking
- 🗺️ **Route optimization**: powered by Valhalla API
- 🏛️ **Cultural data**: real estate, traditions, and town images

---

## 📜 License

MIT © 2025 — Developed for academic and research purposes.
