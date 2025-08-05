from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app_config.logger import get_logger
from app.routes.api import router

logger = get_logger("APP")

version = "v1"
description = """
A REST API for a itinerary generator web service.

This REST API is able to create recommendations using embeddings and generating itineraries.
"""
version_prefix = f"/api/{version}"


app = FastAPI(
    description=description,
    version=version,
    docs_url=f"{version_prefix}/docs",
    contact={
        "name": "Christian Berdejo",
        "url": "https://github.com/cberdejo",
        "email": "cberdejo2205@gmail.com",
    },
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix=version_prefix)
