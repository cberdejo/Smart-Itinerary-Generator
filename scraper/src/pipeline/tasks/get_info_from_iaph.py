from models.municipality import IntangibleAsset, RealEstateAsset
from app_config.logger import get_logger

import asyncio
import httpx
import json
import polars as pl
from prefect import task
from tqdm.asyncio import tqdm_asyncio
from typing import Callable

logger = get_logger(__name__)
headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}


def trim_inmueble(bien: dict) -> RealEstateAsset:
    """
    Transforms a dictionary representing a real estate asset into a `RealEstateAsset` object.
    Args:
        bien (dict): A dictionary containing information about a real estate asset.
                     Expected keys include "identifica", "clob", and "tipologiaList".
    Returns:
        RealEstateAsset: An object containing structured information about the real estate asset.
    The function processes the following keys:
        - "identifica": Extracts details such as name, municipality name, and characterization.
        - "clob": Extracts the description of the asset.
        - "tipologiaList": Extracts typologies, including their names, periods, and ethnicities.
    Notes:
        - If "tipologia" under "tipologiaList" is a dictionary, it is converted into a list.
        - Each typology is structured into a dictionary with keys "den_tipologia", "periodos", and "den_etnia".
    """

    identifica = bien.get("identifica", {})
    clob = bien.get("clob", {})
    tipologia_list = bien.get("tipologiaList", {})
    tipologia = tipologia_list.get("tipologia", [])

    if isinstance(tipologia, dict):
        tipologia = [tipologia]

    tipologias = []
    for t in tipologia:
        if isinstance(t, dict):
            tipologias.append(
                {
                    "den_tipologia": t.get("den_tipologia", ""),
                    "periodos": t.get("periodos", ""),
                    "den_etnia": t.get("den_etnia", ""),
                }
            )

    return RealEstateAsset(
        name=identifica.get("denominacion", ""),
        description=clob.get("descripcion", ""),
        municipality_name=identifica.get("municipio"),
        typologies=tipologias,
        characterization=identifica.get("caracterizacion", ""),
    )


def trim_inmaterial(bien: dict) -> IntangibleAsset:
    """
    Extracts and transforms data from a dictionary representing an intangible asset
    into an IntangibleAsset object.
    Args:
        bien (dict): A dictionary containing information about an intangible asset.
                     Expected keys include "identifica", "clob", and "tipologiaList".
    Returns:
        IntangibleAsset: An object containing the processed data, including name,
                         municipality name, scope, typology, description, and date.
    Notes:
        - The "identifica" key is expected to contain subkeys such as "denominacion",
          "municipio", "ambito", and "fechasact".
        - The "clob" key is expected to contain a "descripcion" subkey.
        - The "tipologiaList" key is expected to contain a "tipologia" subkey, which
          can be either a dictionary or a list of dictionaries. The "den_tipologia"
          value is extracted from the first dictionary in the list if applicable.
    """

    identifica = bien.get("identifica", {})
    clob = bien.get("clob", {})
    tipologia_list = bien.get("tipologiaList", {})
    tipologia = tipologia_list.get("tipologia", {})
    tipologia_name = ""

    if isinstance(tipologia, dict):
        tipologia_name = tipologia.get("den_tipologia", "")
    elif isinstance(tipologia, list) and len(tipologia) > 0:
        tipologia_name = (
            tipologia[0].get("den_tipologia", "")
            if isinstance(tipologia[0], dict)
            else ""
        )

    return IntangibleAsset(
        name=identifica.get("denominacion", ""),
        municipality_name=identifica.get("municipio"),
        scope=identifica.get("ambito", ""),
        typology=tipologia_name,
        description=clob.get("descripcion", ""),
        date=identifica.get("fechasact", ""),
    )


async def fetch_single_bien_async(
    client: httpx.AsyncClient, type_: str, id_: str, retries: int = 3
) -> dict | None:
    """
    Asynchronously fetches detailed information for a single asset ('bien') from the IAPH dataset.

    Args:
        client (httpx.AsyncClient): HTTP client to perform the request.
        type_ (str): Type of asset ("inmueble" or "inmaterial").
        id_ (str): Asset identifier.
        retries (int, optional): Number of retry attempts in case of failure. Defaults to 3.

    Returns:
        dict | None: Parsed JSON data if successful, else None.
    """
    url = f"https://juntadeandalucia.es/datosabiertos/portal/iaph/dataset/bien/{type_}/{id_}"

    for attempt in range(retries):
        try:
            response = await client.get(url)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if response.status_code == 503 and attempt < retries - 1:
                wait_time = 2**attempt
                logger.warning(
                    f"503 received for {type_} ID {id_}, attempt {attempt + 1}/{retries}, retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
                continue
            logger.error(
                f"HTTP error fetching {type_} ID {id_}: {e} (status: {response.status_code})"
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {type_} ID {id_}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {type_} ID {id_}: {e}")
            return None


async def get_full_bienes_data_async(
    type_: str, max_concurrent_requests: int = 10
) -> list:
    assert type_ in ("inmueble", "inmaterial"), (
        f"Invalid type: {type_}. Must be 'inmueble' or 'inmaterial'"
    )

    base_url = (
        f"https://juntadeandalucia.es/datosabiertos/portal/iaph/dataset/bien/{type_}"
    )

    try:
        async with httpx.AsyncClient(
            timeout=30.0, headers=headers, verify=False, follow_redirects=True
        ) as client:
            r = await client.get(base_url)
            r.raise_for_status()
            raw_data = r.json()

            bienes = raw_data.get("inmueble" if type_ == "inmueble" else "bien", [])
            ids = [bien["id"] for bien in bienes if "id" in bien]

            sem = asyncio.Semaphore(max_concurrent_requests)

            async def limited_fetch(id_):
                async with sem:
                    return await fetch_single_bien_async(client, type_, id_)

            tasks = [limited_fetch(id_) for id_ in ids]
            results = await tqdm_asyncio.gather(
                *tasks, desc=f"Downloading {type_}s", unit="bien"
            )

            return [res for res in results if res is not None]

    except Exception as e:
        logger.error(f"Error downloading base list of {type_}s: {e}")
        return []


def safe_map_trim(trim_func: Callable, bienes: list) -> list:
    """
    Applies a trimming function to a list of bienes safely, filtering out errors.

    Args:
        trim_func (Callable): Function to convert raw dict to Pydantic model.
        bienes (list): List of raw asset dictionaries.

    Returns:
        list: List of successfully converted Pydantic models.
    """
    results = []
    for bien in bienes:
        try:
            results.append(trim_func(bien))
        except Exception as e:
            logger.error(f"Error trimming asset {bien.get('id', 'unknown')}: {e}")
    return results


@task
async def get_info_from_iaph() -> dict[str, pl.DataFrame]:
    """
    Retrieves and returns real estate and intangible asset data from IAPH.

    Returns:
        dict[str, pl.DataFrame]: A dictionary containing:
            - "real_estate_assets": A Polars DataFrame with real estate asset data.
            - "intangible": A Polars DataFrame with intangible asset data.

    Raises:
        Any exceptions raised by `get_full_bienes_data_async`.
    """

    real_estate_assets_raw, intangible_assets_raw = await asyncio.gather(
        get_full_bienes_data_async("inmueble"), get_full_bienes_data_async("inmaterial")
    )

    return {
        "real_estate_assets": safe_map_trim(trim_inmueble, real_estate_assets_raw),
        "intangible": safe_map_trim(trim_inmaterial, intangible_assets_raw),
    }
