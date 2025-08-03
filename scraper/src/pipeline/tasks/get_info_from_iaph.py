from models.municipality import IntangibleAsset, RealEstateAsset, RealEstateTypology
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
        - Each typology is structured into a dictionary with keys "den_tipologia", "periodos",  "den_etnia" and "denom_acti".
        - "den_tipologia is mandatory in the tipology dictionary."
    """

    identifica = bien.get("identifica", {})
    clob = bien.get("clob", {})
    tipologia_list = bien.get("tipologiaList", {})
    tipologia = tipologia_list.get("tipologia", [])

    if isinstance(
        tipologia, dict
    ):  # Some assets have directly the tipologia not the list
        tipologia = [tipologia]

    final_tipologia_list: list[RealEstateTypology] = []
    for t in tipologia:
        if isinstance(t, dict) and t.get("den_tipologia"):
            final_tipologia_list.append(
                RealEstateTypology(
                    den_tipologia=str(t.get("den_tipologia", "")),
                    periodos=str(t.get("periodos", "")),
                    den_etnia=str(t.get("den_etnia", "")),
                    denom_acti=str(t.get("denom_acti", "")),
                )
            )

    return RealEstateAsset(
        name=identifica.get("denominacion", ""),
        description=clob.get("descripcion", ""),
        municipality_name=identifica.get("municipio"),
        typologies=final_tipologia_list,
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
            if e.response.status_code in (404, 500):
                logger.warning(f"Empty response for {id_} ({e.response.status_code})")
                return None
            elif e.response.status_code == 503 and attempt < retries - 1:
                # Continue to retry logic below
                pass
            else:
                logger.error(
                    f"HTTP error fetching {type_} ID {id_}: {e} (status: {e.response.status_code})"
                )
                return None

        except (httpx.TimeoutException, httpx.RequestError) as e:
            if attempt < retries - 1:
                # Continue to retry logic below
                pass
            else:
                error_type = (
                    "Timeout"
                    if isinstance(e, httpx.TimeoutException)
                    else "Connection error"
                )
                logger.error(f"{error_type} fetching {type_} ID {id_}: {str(e)}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {type_} ID {id_}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {type_} ID {id_}: {e}")
            return None

        # Retry logic (only reached for retryable errors)
        if attempt < retries - 1:
            wait_time = 2**attempt
            error_msg = (
                "503 received"
                if "e" in locals()
                and hasattr(e, "response")
                and e.response.status_code == 503
                else "Error occurred"
            )
            logger.warning(
                f"{error_msg} for {type_} ID {id_}, attempt {attempt + 1}/{retries}, retrying in {wait_time}s..."
            )
            await asyncio.sleep(wait_time)

    return None


def build_minimal_inmueble(entry: dict) -> dict:
    """
    Creates a stub with the bare minimum so that `trim_inmueble`
    doesn't crash when the detailed file doesn't exist.

    Args:
        entry (dict): Asset entry from the base list.

    Returns:
        dict: Stub for the asset.
    """
    logger.info("building stub for %s", entry["id"])
    return {
        "identifica": {
            "denominacion": entry.get("denominacion"),
            "municipio": entry.get("municipio"),
            "caracterizacion": entry.get("caracterizacion"),
        },
        "clob": {"descripcion": ""},
        "tipologiaList": {"tipologia": []},
    }


def build_minimal_inmaterial(entry: dict) -> dict:
    """
    Stub for intangible assets.  *ambito* and *fechasact* are not
    present in the base list, so we leave them empty.

    Args:
        entry (dict): Asset entry from the base list.

    Returns:
        dict: Stub for the asset.
    """
    return {
        "identifica": {
            "denominacion": entry.get("denominacion"),
            "municipio": entry.get("municipio"),
            "ambito": "",
            "fechasact": "",
        },
        "clob": {"descripcion": ""},
        "tipologiaList": {"tipologia": []},
    }


_build_stub: dict[str, Callable[[dict], dict]] = {
    "inmueble": build_minimal_inmueble,
    "inmaterial": build_minimal_inmaterial,
}


async def get_full_assets_data_async(
    type_: str, max_concurrent_requests: int = 20
) -> list[dict]:
    """
    Downloads detailed information for all assets of a given type from the IAPH dataset.
    1. The base list of assets is first downloaded from the IAPH dataset.
    2. For each asset in the base list, a detail request is made to the IAPH dataset.
    3. If the detail request fails, a minimal stub is returned instead.

    Args:
        type_ (str): Type of asset ("inmueble" or "inmaterial").
        max_concurrent_requests (int, optional): Maximum number of concurrent requests.
            Defaults to 20.

    Returns:
        list[dict]: List of dictionaries, each containing the detailed information
            for an asset of the given type.

    Raises:
        AssertionError: If `type_` is not one of "inmueble" or "inmaterial".

    """
    assert type_ in ("inmueble", "inmaterial")

    base_url = (
        f"https://juntadeandalucia.es/datosabiertos/portal/iaph/dataset/bien/{type_}"
    )

    async with httpx.AsyncClient(
        timeout=30, headers=headers, follow_redirects=True
    ) as client:
        r = await client.get(base_url)
        r.raise_for_status()
        raw_data = r.json()

        bienes_base = raw_data["inmueble" if type_ == "inmueble" else "bien"]

        sem = asyncio.Semaphore(max_concurrent_requests)
        build_stub = _build_stub[type_]

        async def limited_fetch(entry: dict) -> dict:
            async with sem:
                detail = await fetch_single_bien_async(client, type_, entry["id"])
                return detail or build_stub(entry)

        tasks = [limited_fetch(entry) for entry in bienes_base]
        return await tqdm_asyncio.gather(
            *tasks, desc=f"Descargando {type_}s", unit="bien"
        )


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
        get_full_assets_data_async("inmueble"), get_full_assets_data_async("inmaterial")
    )

    return {
        "real_estate_assets": safe_map_trim(trim_inmueble, real_estate_assets_raw),
        "intangible": safe_map_trim(trim_inmaterial, intangible_assets_raw),
    }
