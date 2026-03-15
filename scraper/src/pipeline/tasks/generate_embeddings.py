from typing import List
from tqdm import tqdm
from prefect import task

from models.db_models import Town, Intangible, RealEstate, Image
from models.municipality import MunicipalityInfo
from config.logger import get_logger
from helpers.embedder import get_embedding
from helpers.hybrid_search import build_search_texts_from_municipalities

logger = get_logger("generate_embeddings")


def _to_float_list(vector) -> list[float]:
    if hasattr(vector, "tolist"):
        vector = vector.tolist()
    return [float(value) for value in vector]


@task
def generate_embeddings(
    municipalities: List[MunicipalityInfo], batch_size: int = 32
) -> tuple[List[Town], List[Intangible], List[RealEstate], List[Image]]:
    """
    Generate embeddings for a list of municipalities and create corresponding database objects.
    This function processes a list of MunicipalityInfo objects, generates embeddings using
    the configured embedding backend, and creates SQLAlchemy objects for towns, intangible assets,
    and real estate assets. The processing is done in batches to optimize performance.
    Args:
        municipalities (List[MunicipalityInfo]): A list of MunicipalityInfo objects containing
            information about municipalities.
    Returns:
        Tuple[List[Town], List[Intangible], List[RealEstate], List[ImageTown]]: A tuple containing
            lists of Town, Intangible, RealEstate, and ImageTown objects.
    Raises:
        Exception: Any unexpected errors during embedding generation or object creation are logged.
    """

    if not municipalities:
        logger.warning("No municipalities provided to generate embeddings")
        return ([], [], [], [])

    towns: List[Town] = []
    intangible_assets: List[Intangible] = []
    real_estate_assets: List[RealEstate] = []
    images: List[Image] = []

    total_items = len(municipalities)

    # Process in batches
    for batch_start in tqdm(
        range(0, total_items, batch_size), desc="Processing batches"
    ):
        batch_end = min(batch_start + batch_size, total_items)
        current_batch = municipalities[batch_start:batch_end]

        try:
            # Canonical text shared with backend retrieval (dense + sparse alignment)
            batch_strings = build_search_texts_from_municipalities(current_batch)
            batch_embeddings = get_embedding(batch_strings)

            # Create Objects SQLAlchemy
            for offset, (municipality, embedding) in enumerate(
                zip(current_batch, batch_embeddings)
            ):
                try:
                    # ----- Town --------------------------------------------------
                    town = Town(
                        municipality_ine=str(municipality.ine),
                        municipality_name=municipality.name,
                        capital_city=municipality.capital,
                        latitude=municipality.latitude,
                        longitude=municipality.longitude,
                        province_identifier=(
                            str(municipality.province_identifier)
                            if municipality.province_identifier is not None
                            else None
                        ),
                        description=municipality.description,
                        history=municipality.history,
                        province_name=getattr(municipality, "province_name", None),
                        has_beach=municipality.has_beach,
                        embeddings=_to_float_list(embedding),
                    )
                    towns.append(town)

                    # ----- Intangible-------------------------------------
                    if municipality.intangible_assets:
                        for asset in municipality.intangible_assets:
                            intangible_assets.append(
                                Intangible(
                                    municipality_ine=str(municipality.ine),
                                    name=asset.name,
                                    scope=asset.scope,
                                    typology=asset.typology_string(),
                                    description=asset.description,
                                    date=asset.date,
                                )
                            )

                    # ----- RealEstate-------------------------------------
                    if municipality.real_estate_assets:
                        for asset in municipality.real_estate_assets:
                            real_estate_assets.append(
                                RealEstate(
                                    municipality_ine=str(municipality.ine),
                                    name=asset.name,
                                    description=asset.description,
                                    typologies=[
                                        t.model_dump() for t in asset.typologies
                                    ]
                                    if asset.typologies
                                    else [],
                                    characterization=asset.characterization,
                                )
                            )

                    # ----- Images-------------------------------------
                    if municipality.images:
                        for url in municipality.images:
                            images.append(
                                Image(
                                    municipality_ine=str(municipality.ine),
                                    url=url,
                                )
                            )

                except Exception as e:
                    logger.warning(
                        f"Error creating objects for municipality index "
                        f"{batch_start + offset}: {e}"
                    )

        except Exception as e:
            logger.error(f"Error processing batch {batch_start}-{batch_end}: {e}")
    return towns, intangible_assets, real_estate_assets, images
