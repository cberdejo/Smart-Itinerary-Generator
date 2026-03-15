from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import threading
import time
import re

from helpers.selenium import get_driver
from unidecode import unidecode

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
)

from prefect import task
from tqdm import tqdm
from multiprocessing import cpu_count

from config.logger import get_logger

logger = get_logger(__name__)

#######################################################################################
# ─────────────────────────────── Scraping helpers ────────────────────────────────────
#######################################################################################

# global variables for crawl delay management
_crawl_delay_lock = threading.Lock()
_last_request_time = 0


def ensure_crawl_delay(min_delay: float = 2.0):
    """
    Ensure a minimum time has passed since the last call to this function
    before continuing. This is useful to control the crawl delay between
    requests to the same website.

    Args:
        min_delay: The minimum time (in seconds) that should have passed
        since the last call to this function. If the time since the last call
        is less than this value, the function will sleep for the difference
        between the two times.
    """
    global _last_request_time

    with _crawl_delay_lock:
        current_time = time.time()
        time_since_last = current_time - _last_request_time

        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            time.sleep(sleep_time)

        _last_request_time = time.time()


def accept_cookies_if_present(driver: WebDriver, verbose: bool = False) -> None:
    """
    Attempts to accept cookies if the relevant button is present.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        verbose (bool): Enables logging.
    Raises:
        Exception: If the cookie acceptance button is not found.
    """
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[@mode='primary' and .//span[contains(translate(text(),'acepto','ACEPTO'),'ACEPTO')]]",
                )
            )
        )
        driver.execute_script("arguments[0].click();", accept_btn)
        if verbose:
            logger.info("Cookies accepted")
    except Exception:
        if verbose:
            logger.warning("Cookie acceptance button not found")


def get_paragraphs_before_section_h2(driver: WebDriver, section_name: str) -> str:
    """
    Extracts paragraphs before a specified H2 section.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        section_name (str): The name of the H2 section.
    Returns:
        str: Concatenated paragraphs before the specified section.
    """
    try:
        paragraphs = driver.find_elements(
            By.XPATH, f"//h2[normalize-space()='{section_name}']/preceding-sibling::p"
        )
        return "\n\n".join(p.text.strip() for p in paragraphs if p.text.strip())
    except Exception as e:
        logger.error(
            f"Error extracting paragraphs before section '{section_name}': {e}"
        )
        return ""


def get_paragraphs_after_section_h2(driver: WebDriver, section_name: str) -> str:
    """
    Extracts paragraphs after a specified H2 section.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        section_name (str): The name of the H2 section.
    Returns:
        str: Concatenated paragraphs after the specified section.
    """
    try:
        paragraphs = []
        content = driver.find_elements(By.XPATH, "//h2 | //p")
        found = False

        for element in content:
            tag = element.tag_name.lower()
            text = element.text.strip()

            if tag == "h2" and section_name.lower() in text.lower():
                found = True
                continue
            if found:
                if tag == "h2":
                    break
                if tag == "p" and text:
                    paragraphs.append(text)

        return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Error extracting paragraphs after section '{section_name}': {e}")
        return ""


def extract_images(driver: WebDriver) -> list[str]:
    """
    Extracts image URLs from the detail gallery section.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
    Returns:
        List[str]: List of unique image URLs.
    """
    images = []
    try:
        img_elements = driver.find_elements(
            By.CSS_SELECTOR,
            "div.detail-gallery div.slider-cont:not(.slider-thumbnails) picture img",
        )

        for img in img_elements:
            src = img.get_attribute("src")
            if src and src not in images:
                images.append(src)
    except Exception as e:
        logger.error(f"Error extracting images: {e}")

    return images


#######################################################################################
# ─────────────────────────────── Scraping Url ────────────────────────────────────
#######################################################################################
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((WebDriverException, TimeoutException)),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying due to: {retry_state.outcome.exception()} "
        f"(attempt {retry_state.attempt_number})"
    ),
)
def scrap_tourism_url(
    driver: WebDriver,
    url: str,
    verbose: bool = False,
    respect_crawl_delay: bool = True,
) -> dict | None:
    """
    Main scraper function for processing tourism URLs.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        url (str): URL to scrape.
        verbose (bool): Enable verbose logging.
        respect_crawl_delay (bool): Whether to respect crawl delay.

    Returns:
        dict: Extracted tourism information.
    """

    try:
        if respect_crawl_delay:
            ensure_crawl_delay()
        else:
            # Introduce a random delay to avoid detection
            time.sleep(random.uniform(0.5, 1.5))

        if not driver or driver.session_id is None:
            logger.error(f"Driver is not valid for URL: {url}")
            raise WebDriverException("Invalid driver session")

        try:
            driver.get(url)
        except TimeoutException as e:
            logger.error("Timeout loading %s: %s", url, e)
            raise
        except WebDriverException as e:
            logger.error("WebDriverException loading %s:\n%s", url, e)
            raise
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        if verbose:
            logger.info(f"Scrapping: {url}")

        accept_cookies_if_present(driver, verbose=verbose)

        description = get_paragraphs_before_section_h2(driver, "Historia")
        history = get_paragraphs_after_section_h2(driver, "Historia")
        images = extract_images(driver)
        if verbose:
            logger.info(f"Description: {description[:60]}...")
            logger.info(f"History: {history[:60]}...")
            logger.info(f"Images: {len(images)}")

        return {
            "description": description,
            "history": history,
            "images": images,
        }

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise


def normalize_name(name: str) -> str:
    """
    Normalizes a string by removing special characters and converting to lowercase.

    Args:
        name (str): The input string to be normalized.

    Returns:
        str: The normalized string.
    """
    name = unidecode(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name


#######################################################################################
# ─────────────────────────────── Batch processing ────────────────────────────────────
#######################################################################################


def process_batch(
    batch: list[dict],
    batch_num: int,
    respect_crawl_delay: bool = False,
) -> list[dict]:
    """
    Process a batch of towns and scrape their info from Andalucia.org.

    Args:
        batch (list[dict]): A list of dictionaries, each with a "municipality_name" key.
        batch_num (int): The batch number, for logging purposes.
        respect_crawl_delay (bool): If True, will enforce a delay between scraping pages.

    Returns:
        list[dict]: The list of towns with their info enriched with the scraped data.
    """
    base_url = "https://andalucia.org/es/"

    logger.info("Batch %s - starting with %d towns", batch_num, len(batch))

    try:
        driver = get_driver(headless=True)
    except Exception as e:
        logger.error("Batch %s - Chrome failed to start: %s", batch_num, e)
        # Mark every town as failed
        for t in batch:
            t.update({"description": None, "history": None, "images": []})
        return batch

    enriched: list[dict] = []

    for town in tqdm(batch, desc=f"Batch {batch_num}", total=len(batch)):
        name = town.get("municipality_name")
        if not name:
            logger.warning("Batch %s - missing municipality_name", batch_num)
            enriched.append(town)
            continue

        url = f"{base_url}{normalize_name(name)}"

        try:
            scraped = scrap_tourism_url(
                driver, url, respect_crawl_delay=respect_crawl_delay
            )
            town.update(
                scraped
                if scraped
                else {"description": None, "history": None, "images": []}
            )
        except Exception as e:
            with open("failed_pages.log", "a") as f:
                f.write(url + "\n")

            logger.error("Batch %s - error scraping %s: %s", batch_num, url, e)
            town.update({"description": None, "history": None, "images": []})

        enriched.append(town)

    try:
        driver.quit()
    except Exception:
        logger.error("Batch %s - error quitting driver", batch_num)

    return enriched


#######################################################################################
# ─────────────────────────────── Prefect task ────────────────────────────────────────
#######################################################################################


@task
def get_towns_info_from_turismo_andalucia(
    towns: list[dict],
    respect_crawl_delay: bool = False,
    max_workers: int = min(8, cpu_count() * 2),
    batch_size: int = 50,
) -> list[dict]:
    """
    Enrich ``towns`` with tourism data from andalucia.org.

    Each batch is processed by a dedicated Chrome instance.  The number of
    concurrent instances is capped by ``max_workers``.
    Args:
        towns (list[dict]): List of towns to enrich.
        respect_crawl_delay (bool, optional): If True, respect the crawl delay
            between requests. Defaults to False.
        max_workers (int, optional): Maximum number of concurrent workers.
            Defaults to 4.
        batch_size (int, optional): Number of towns to process in  each batch.
            Defaults to 100.
    Returns:
        list[dict]: List of enriched towns with tourism data.
    """

    batches = [towns[i : i + batch_size] for i in range(0, len(towns), batch_size)]
    # limited_batches = batches[:1]

    total_batches = len(batches)
    if respect_crawl_delay:
        max_workers = 1

    logger.info(
        "Processing %d towns in %d batches of %d (max workers =%d)",
        len(towns),
        total_batches,
        batch_size,
        max_workers,
    )

    all_enriched: list[dict] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(
                process_batch,
                batch,
                i + 1,
                respect_crawl_delay=respect_crawl_delay,
            ): i + 1
            for i, batch in enumerate(batches)
        }

        for future in tqdm(
            as_completed(future_to_id),
            total=len(future_to_id),
            desc="Batches",
        ):
            batch_id = future_to_id[future]
            try:
                result = future.result()
            except Exception as exc:
                logger.exception(
                    "Unhandled error in batch %s, marking towns as failed: %s",
                    batch_id,
                    exc,
                )
                # Fallback – preserve order
                result = [
                    {
                        **town,
                        "description": None,
                        "history": None,
                        "images": [],
                    }
                    for town in batches[batch_id - 1]
                ]
            all_enriched.extend(result)

    logger.info("Completed processing %d towns", len(all_enriched))
    return all_enriched
