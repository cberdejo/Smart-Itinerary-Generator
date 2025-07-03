# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager


# def init_selenium(headless: bool = True) -> webdriver.Chrome:
#     """
#     Initializes and configures a Selenium Chrome WebDriver instance.

#     Args:
#         headless (bool): Whether to run in headless mode.

#     Returns:
#         webdriver.Chrome: Configured WebDriver instance.
#     """
#     options = Options()
#     if headless:
#         options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("window-size=1920,1080")

#     driver = webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=options,
#     )

#     return driver


# class SeleniumDriver:
#     """
#     Context manager for Selenium WebDriver lifecycle.
#     Automatically initializes and quits the driver.
#     """

#     def __init__(self, headless: bool = True):
#         self.headless = headless
#         self.driver = None

#     def __enter__(self) -> webdriver.Chrome:
#         self.driver = init_selenium(headless=self.headless)
#         return self.driver

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         if self.driver:
#             self.driver.quit()

import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
from app_config.logger import get_logger

logger = get_logger(__name__)

# Thread‑local storage to keep one driver per thread
_thread_local = threading.local()
# We also keep a global registry so that we can shut every driver down cleanly at the end
_driver_pool: list[webdriver.Chrome] = []


def init_selenium(headless: bool = True) -> webdriver.Chrome:
    """Create and configure a Chrome driver instance."""
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    return driver


def get_driver(headless: bool = True) -> webdriver.Chrome:
    """Return *one* persistent driver per worker thread.

    The first time a thread calls this function we create a driver and store it in
    thread‑local storage. Subsequent calls from the same thread return the same
    instance, so the browser is kept open for the entire lifetime of that worker.
    """
    driver = getattr(_thread_local, "driver", None)
    if driver is None:
        driver = init_selenium(headless=headless)
        _thread_local.driver = driver
        _driver_pool.append(driver)
    return driver


def close_all_drivers() -> None:
    """Quit every ChromeDriver we started (called once when all work is done)."""
    for d in _driver_pool:
        try:
            d.quit()
        except Exception:
            # We do not want a single failure here to mask others
            logger.exception("Error while quitting driver")
    _driver_pool.clear()
