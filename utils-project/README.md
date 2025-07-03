# Utils Project

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-504848?style=for-the-badge&logo=sqlalchemy&logoColor=white)

This module provides common utilities for both the `backend` and `scraper` modules, including PostgreSQL database configuration, a logging system, and ORM models representing Andalusian municipalities, their images, and their tangible and intangible heritage.

---

## ⚙️ Features

- 🔧 Database configuration using SQLAlchemy (`app_config/postgres.py`)
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
│  │  ├─ logger.py              # Logger configuration
│  │  └─ postgres.py            # PostgreSQL engine and session setup
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
