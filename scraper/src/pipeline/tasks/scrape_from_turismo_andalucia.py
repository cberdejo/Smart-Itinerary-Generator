import time
import re
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from helpers.selenium import close_all_drivers, get_driver
from unidecode import unidecode

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from prefect import task
from tqdm import tqdm

from app_config.logger import get_logger

logger = get_logger(__name__)


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
    Raises:
        Exception: If the section is not found or if an error occurs during extraction.
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
    """ "
    Extracts paragraphs after a specified H2 section.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        section_name (str): The name of the H2 section.
    Returns:
        str: Concatenated paragraphs after the specified section.
    Raises:
        Exception: If the section is not found or if an error occurs during extraction.
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
    Raises:
        Exception: If the image elements cannot be found or if an error occurs during extraction.

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


def scrap_tourism_url(
    driver: WebDriver,
    url: str,
    verbose: bool = False,
) -> Dict | None:
    """
    Main scraper function for processing multiple tourism URLs.

    Args:
        urls (List[str]): List of URLs to scrape.
        verbose (bool): Enable verbose logging.
        headless (bool): Whether to run browser in headless mode.

    Returns:
        List[dict]: Extracted tourism information.
    """

    driver.get(url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

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


@task
def get_towns_info_from_turismo_andalucia(
    towns: list[dict], max_workers: int = 4
) -> list[dict]:
    """
    Scrapes tourism information from multiple URLs using a ThreadPoolExecutor.

    Args:
        urls (List[str]): List of URLs to scrape.
        max_workers (int): Maximum number of threads to use in the ThreadPoolExecutor.

    Returns:
        List[dict]: Extracted tourism information.
    """

    base_url = "https://andalucia.org/es/"
    enriched: list[dict] = []

    def worker(town: dict) -> dict:
        name = town.get("municipality_name")
        if not name:
            logger.warning("municipality_name not found")
            return town

        normalized_name = normalize_name(name)
        url = f"{base_url}{normalized_name}"
        driver = get_driver(headless=True)

        # `scrap_tourism_url` must accept an existing driver (or be adapted accordingly)
        try:
            scraped = scrap_tourism_url(driver=driver, url=url, verbose=False)
        except Exception as e:
            logger.error("Error scraping %s: %s", url, e)
            scraped = None

        if scraped is None:
            logger.warning("Could not scrape %s", url)
            town.update(
                {
                    "description": None,
                    "history": None,
                    "images": [],
                }
            )
        else:
            town.update(scraped)

        time.sleep(2)  # Crawl delay
        return town

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, town) for town in towns]
            for future in tqdm(
                as_completed(futures), total=len(towns), desc="Scraping turismo info"
            ):
                enriched.append(future.result())
    finally:
        # Make sure we always release browser processes, even if something fails.
        close_all_drivers()

    return enriched
