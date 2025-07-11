from typing import List
from tqdm import tqdm
from prefect import task

from db_models import Town, Intangible, RealEstate, ImageTown
from models.municipality import MunicipalityInfo
from app_config.logger import get_logger
from app_helpers.embedder import get_embedding

logger = get_logger("generate_embeddings")


@task
def generate_embeddings(
    municipalities: List[MunicipalityInfo],
) -> tuple[List[Town], List[Intangible], List[RealEstate], List[ImageTown]]:
    """
    Generate embeddings for a list of municipalities and create corresponding database objects.
    This function processes a list of MunicipalityInfo objects, generates embeddings using
    the SentenceTransformer model, and creates SQLAlchemy objects for towns, intangible assets,
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
        return []

    BATCH_SIZE = 32

    towns: List[Town] = []
    intangible_assets: List[Intangible] = []
    real_estate_assets: List[RealEstate] = []
    images: List[ImageTown] = []

    total_items = len(municipalities)

    # Process in batches
    for batch_start in tqdm(
        range(0, total_items, BATCH_SIZE), desc="Processing batches"
    ):
        batch_end = min(batch_start + BATCH_SIZE, total_items)
        current_batch = municipalities[batch_start:batch_end]

        try:
            batch_strings = [item.get_embedding_text() for item in current_batch]
            batch_embeddings = get_embedding(batch_strings)

            # Create Objects SQLAlchemy
            for offset, (municipality, embedding) in enumerate(
                zip(current_batch, batch_embeddings)
            ):
                try:
                    print(embedding)
                    # ----- Town --------------------------------------------------
                    town = Town(
                        municipality_ine=municipality.ine,
                        municipality_name=municipality.name,
                        capital_city=municipality.capital,
                        latitude=municipality.latitude,
                        longitude=municipality.longitude,
                        province_identifier=getattr(
                            municipality, "province_identifier", None
                        ),
                        description=municipality.description,
                        history=municipality.history,
                        province_name=getattr(municipality, "province_name", None),
                        has_beach=municipality.has_beach,
                        embeddings=embedding.tolist(),
                    )
                    towns.append(town)

                    # ----- Intangible-------------------------------------
                    if municipality.intangible_assets:
                        for asset in municipality.intangible_assets:
                            intangible_assets.append(
                                Intangible(
                                    municipality_ine=municipality.ine,
                                    name=asset.name,
                                    scope=asset.scope,
                                    typology=asset.typology,
                                    description=asset.description,
                                    date=asset.date,
                                )
                            )

                    # ----- RealEstate-------------------------------------
                    if municipality.real_estate_assets:
                        for asset in municipality.real_estate_assets:
                            real_estate_assets.append(
                                RealEstate(
                                    municipality_ine=municipality.ine,
                                    name=asset.name,
                                    description=asset.description,
                                    typologies=asset.typologies,
                                    characterization=asset.characterization,
                                )
                            )

                    # ----- Images-------------------------------------
                    if municipality.images:
                        for url in municipality.images:
                            images.append(
                                ImageTown(
                                    municipality_ine=municipality.ine,
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
