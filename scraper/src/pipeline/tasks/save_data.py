# utils/db/load_to_postgres.py
from typing import List, Sequence, Iterable, Dict, Any, Union
from itertools import islice

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app_config.logger import get_logger
from helpers.postgres import get_engine, get_session
from db_models import Town, Intangible, RealEstate, ImageTown, Base
from prefect import task

logger = get_logger("load_to_postgres")


def chunked(iterable: Iterable, size: int) -> Iterable[Sequence]:
    """
    The `chunked` function is a utility that divides an iterable into smaller chunks of a specified size.

    Usage:
        This function is typically used to process large datasets in smaller, more manageable pieces,
        which can be particularly useful when working with database transactions or batch processing tasks.

    Args:
        iterable (Iterable): The input data that needs to be divided into chunks.
        size (int): The size of each chunk. Determines the maximum number of items in each chunk.

    Returns:
        Iterable[Sequence]: A generator that yields chunks (sequences) of the specified size until the iterable is exhausted.
    """
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


def model_to_dict(model_instance) -> Dict[str, Any]:
    """
    Converts a SQLAlchemy model instance to a dictionary.

    Args:
        model_instance: SQLAlchemy model instance

    Returns:
        Dict[str, Any]: Dictionary representation of the model
    """
    if hasattr(model_instance, "__dict__"):
        # Remove SQLAlchemy internal attributes
        return {
            key: value
            for key, value in model_instance.__dict__.items()
            if not key.startswith("_")
        }
    elif hasattr(model_instance, "dict"):
        # Pydantic model
        return model_instance.dict()
    else:
        # Assume it's already a dict
        return model_instance


def build_upsert_stmt(model, rows: List[Union[Dict, Any]], conflict_cols: List[str]):
    """
    Builds an upsert statement for SQLAlchemy.

    Args:
        model: SQLAlchemy model to be upserted.
        rows: List of dictionaries or model instances containing the data to be upserted.
        conflict_cols: List of column names used to determine uniqueness.

    Returns:
        A pg_insert statement with a do_update clause.
    """
    # Convert model instances to dictionaries if needed
    dict_rows = []
    for row in rows:
        if isinstance(row, dict):
            dict_rows.append(row)
        else:
            dict_rows.append(model_to_dict(row))

    stmt = pg_insert(model).values(dict_rows)

    # Build update columns excluding conflict columns
    update_cols = {
        col.name: stmt.excluded[col.name]
        for col in model.__table__.columns
        if col.name not in conflict_cols
    }

    if not update_cols:
        return stmt.on_conflict_do_nothing(index_elements=conflict_cols)

    return stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_cols)


def deduplicate_records(records: List[Any], key_func) -> List[Any]:
    """
    Deduplicates records based on a key function.

    Args:
        records: List of records to deduplicate
        key_func: Function that extracts the key for deduplication

    Returns:
        List of deduplicated records
    """
    seen = set()
    deduplicated = []

    for record in records:
        key = key_func(record)
        if key not in seen:
            seen.add(key)
            deduplicated.append(record)
        else:
            logger.warning(f"Duplicate record found and skipped: {key}")

    return deduplicated


# ──────────────────────────────────────────────────────────────────────────────
# Main loader
# ──────────────────────────────────────────────────────────────────────────────
@task
def load_info_to_postgres(
    pg_uri: str,
    new_towns: List[Town],
    new_intangible_assets: List[Intangible],
    new_real_estate_assets: List[RealEstate],
    new_images: List[ImageTown],
    batch_size: int = 1_000,
) -> int:
    """
    Loads data into a PostgreSQL database by performing batch upserts for towns,
    intangible assets, and real estate assets. Deduplication is applied to avoid
    inserting duplicate records.
    Args:
        new_towns (List[TownDB]): List of town records to be inserted or updated.
        new_intangible_assets (List[IntangibleAssetDB]): List of intangible asset
            records to be inserted or updated.
        new_real_estate_assets (List[RealEstateAssetDB]): List of real estate asset
            records to be inserted or updated.
        batch_size (int, optional): Number of records to process in each batch.
            Defaults to 1,000.
        new_images (List[ImageTown]): List of image records to be inserted or updated.
        pg_uri (str, optional): Connection string for the PostgreSQL database.
            Defaults to "postgresql+psycopg2://your_user:your_password@your_host:port/your_database".
    Returns:
        int: Returns 0 if the operation is successful, or 1 if an error occurs.
    Raises:
        RuntimeError: If there is an error connecting to the database.
        SQLAlchemyError: If a database error occurs during execution.
        Exception: If an unexpected error occurs.
    Notes:
        - Deduplication for towns is based on the `municipality_ine` field.
        - Deduplication for intangible assets is based on the combination of
          `municipality_ine` and `name` fields.
        - Deduplication for real estate assets is based on the combination of
          `municipality_ine` and `name` fields.
        - The function commits all changes to the database at the end of the process.
        - In case of an error, the transaction is rolled back to maintain data integrity.
    """
    session = None

    try:
        engine = get_engine(pg_uri)
        Base.metadata.create_all(engine)  # Create tables if they don't exist
        session: Session = get_session(engine)
    except Exception as e:
        raise RuntimeError(f"Error connecting to database: {e}") from e

    try:
        total_processed = 0

        # ---------------------- 1. Towns -------------------------------------
        if new_towns:
            logger.info(f"Processing {len(new_towns)} towns...")

            # Deduplicate towns by municipality_ine
            deduplicated_towns = deduplicate_records(
                new_towns,
                key_func=lambda x: x.municipality_ine
                if hasattr(x, "municipality_ine")
                else x.get("municipality_ine"),
            )

            towns_processed = 0
            for chunk in chunked(deduplicated_towns, batch_size):
                stmt = build_upsert_stmt(
                    Town, chunk, conflict_cols=["municipality_ine"]
                )
                result = session.execute(stmt)
                towns_processed += len(chunk)
                logger.debug(
                    f"Processed {towns_processed}/{len(deduplicated_towns)} towns"
                )

            total_processed += len(deduplicated_towns)
            logger.info(f"Successfully processed {len(deduplicated_towns)} towns")

        # ---------------------- 2. Intangible assets -------------------------
        if new_intangible_assets:
            logger.info(f"Processing {len(new_intangible_assets)} intangible assets...")

            # Deduplicate intangible assets by (municipality_ine, name)
            deduplicated_intangible = deduplicate_records(
                new_intangible_assets,
                key_func=lambda x: (
                    x.municipality_ine
                    if hasattr(x, "municipality_ine")
                    else x.get("municipality_ine"),
                    x.name if hasattr(x, "name") else x.get("name"),
                ),
            )

            intangible_processed = 0
            for chunk in chunked(deduplicated_intangible, batch_size):
                stmt = build_upsert_stmt(
                    Intangible, chunk, conflict_cols=["municipality_ine", "name"]
                )
                result = session.execute(stmt)
                intangible_processed += len(chunk)
                logger.debug(
                    f"Processed {intangible_processed}/{len(deduplicated_intangible)} intangible assets"
                )

            total_processed += len(deduplicated_intangible)
            logger.info(
                f"Successfully processed {len(deduplicated_intangible)} intangible assets"
            )

        # ---------------------- 3. Real-estate assets ------------------------
        if new_real_estate_assets:
            logger.info(
                f"Processing {len(new_real_estate_assets)} real estate assets..."
            )

            # Deduplicate real estate assets by (municipality_ine, name)
            deduplicated_real_estate = deduplicate_records(
                new_real_estate_assets,
                key_func=lambda x: (
                    x.municipality_ine
                    if hasattr(x, "municipality_ine")
                    else x.get("municipality_ine"),
                    x.name if hasattr(x, "name") else x.get("name"),
                ),
            )

            real_estate_processed = 0
            for chunk in chunked(deduplicated_real_estate, batch_size):
                stmt = build_upsert_stmt(
                    RealEstate, chunk, conflict_cols=["municipality_ine", "name"]
                )
                result = session.execute(stmt)
                real_estate_processed += len(chunk)
                logger.debug(
                    f"Processed {real_estate_processed}/{len(deduplicated_real_estate)} real estate assets"
                )

            total_processed += len(deduplicated_real_estate)
            logger.info(
                f"Successfully processed {len(deduplicated_real_estate)} real estate assets"
            )

        # ---------------------- 4. Images  ------------------------
        if new_images:
            logger.info(f"Processing {len(new_images)} images...")

            stmt = build_upsert_stmt(
                ImageTown, new_images, conflict_cols=["municipality_ine", "url"]
            )

            result = session.execute(stmt)

            total_processed += len(new_images)
            logger.info(f"Successfully processed {len(new_images)} images")

        session.commit()
        logger.info(
            f"All data committed successfully. Total records processed: {total_processed}"
        )
        return 0

    except SQLAlchemyError as e:
        if session:
            session.rollback()
        logger.error(f"Database error, rolled back: {e}")
        return 1
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Unexpected error, rolled back: {e}")
        return 1
    finally:
        if session:
            session.close()
