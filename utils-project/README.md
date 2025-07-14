# Utils Project

This module provides common utilities for both the `backend` and `scraper` modules, including , a logging system, and ORM models representing Andalusian municipalities, and their tangible and intangible heritage assets.

---

## ⚙️ Features

- 🧾 Configurable logging system (`app_config/logger.py`)
- 🏛️ Data models for:
  - Municipalities (`town.py`)
  - Intangible heritage assets (`intangible.py`)
  - Real estate heritage assets (`real_estate.py`)
  - Municipality-related images (`image_town.py`)
---

## 🗂️ Project Structure

```
utils-project/
├─ src/
│  ├─ app_config/
│  │  ├─ postgres.py            
│  │  ├─ logger.py              # Logger configuration
│  ├─ app_helpers/
│  │  ├─ embedder.py            # Model for creating embedding
│  ├─ db_models/
│  │  ├─ town.py                # Main municipality model
│  │  ├─ intangible.py          # Intangible heritage model
│  │  ├─ real_estate.py         # Real estate model
│  │  ├─ image_town.py          # Municipality image model
│  │  └─ __init__.py
│  └─ __init__.py
├─ .python-version
├─ pyproject.toml
├─ README.md
└─ uv.lock
```


## 🧠 ORM Models

Models are defined using SQLAlchemy and allow structured data mapping to PostgreSQL tables.

- `Town`: Andalusian municipality with name, location, history, and relationships to images and heritage.
- `Intangible`: intangible cultural asset linked to a municipality.
- `RealEstate`: architectural heritage asset.
- `ImageTown`: image associated with a municipality.

![models](../screenshots/postgres.png)

---

## 📝 Notes

This module is **not intended to run standalone**. It is designed to be used from the `scraper` and `backend` modules, which import it as a shared dependency.

---

## 📄 License

MIT – free to use, modify, and distribute.
