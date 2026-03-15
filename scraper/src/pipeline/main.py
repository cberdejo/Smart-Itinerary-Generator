import os
import time

import httpx
from prefect import flow
from prefect.task_runners import ConcurrentTaskRunner

from config.logger import get_logger
from models.municipality import MunicipalityInfo

from pipeline.tasks.scrape_from_turismo_andalucia import (
    get_towns_info_from_turismo_andalucia,
)
from pipeline.tasks.get_andalusia_towns_ubi_and_name import (
    get_municipality_name_and_ubi,
)
from pipeline.tasks.get_info_from_iaph import get_info_from_iaph
from pipeline.tasks.merge_municipality_info import build_municipality_info_list
from pipeline.tasks.wikipedia_beach_check import get_towns_with_beaches_from_wikipedia
from pipeline.tasks.generate_embeddings import generate_embeddings
from pipeline.tasks.save_data import load_info_to_postgres
from pipeline.tasks.upload_report import save_task_metadata_to_minio


@flow(
    name="Town Scraper",
    retries=3,
    retry_delay_seconds=5,
    task_runner=ConcurrentTaskRunner(),
)
def main():
    # Get municipalities and ubi
    towns_data = get_municipality_name_and_ubi()
    # Enrich Data with Andalusian turism web page
    towns_info_enriched = get_towns_info_from_turismo_andalucia(towns_data)

    # Get Municipalities with beaches and IAPH data concurrently
    beach_map_future = get_towns_with_beaches_from_wikipedia.submit()
    iaph_data_future = get_info_from_iaph.submit()

    beach_map = beach_map_future.result()
    iaph_data = iaph_data_future.result()

    # Merge all info in list of MunicipalityInfo
    municipality_info_list: list[MunicipalityInfo] = build_municipality_info_list(
        towns_data=towns_info_enriched,
        beach_towns=beach_map,
        iaph_data=iaph_data,
    )

    # Generate embeddings and create pydantic objects
    towns, intangible_assets, real_estate_assets, images = generate_embeddings(
        municipality_info_list
    )

    # Save data in DB
    load_info_to_postgres(towns, intangible_assets, real_estate_assets, images)

    # Upload task report in minio
    save_task_metadata_to_minio.submit().result()  # await


if __name__ == "__main__":
    wait_for_prefect_api()
    main()
