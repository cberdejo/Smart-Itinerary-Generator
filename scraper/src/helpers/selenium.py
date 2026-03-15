import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from config.logger import get_logger

logger = get_logger(__name__)

_thread_local = threading.local()
_driver_pool: list[webdriver.Chrome] = []


def init_selenium(headless: bool = True) -> webdriver.Chrome:
    """
    Initializes and returns a Selenium Chrome WebDriver instance with configurable headless mode.
    Args:
        headless (bool, optional): If True, runs Chrome in headless mode with additional options for efficiency and reduced resource usage. Defaults to True.
    Returns:
        webdriver.Chrome: An instance of Chrome WebDriver configured with the specified options.
    """

    options = Options()
    if headless:
        options.add_argument("--headless")  # Run Chrome in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--enable-unsafe-swiftshader")

        # options to disable features for headless mode and efficiency
        options.add_argument("--memory-pressure-off")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-logging")
        options.add_argument("--mute-audio")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=options,
    )

    return driver


def is_driver_alive(driver: webdriver.Chrome) -> bool:
    """
    Check if the given Selenium WebDriver instance is still alive and connected.
    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance to check.
    Returns:
        bool: True if the driver is alive and has a valid session, False otherwise.
    """

    try:
        return driver.service.is_connectable() and driver.session_id is not None
    except Exception:
        return False


def get_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Returns a thread-local instance of a Selenium Chrome WebDriver.
    If a driver does not exist for the current thread or the existing driver is not alive,

    a new driver is initialized (optionally in headless mode), stored in thread-local storage,
    and added to the global driver pool.
    Args:
        headless (bool, optional): Whether to run Chrome in headless mode. Defaults to True.
    Returns:
        webdriver.Chrome: A Selenium Chrome WebDriver instance for the current thread.
    """

    driver = getattr(_thread_local, "driver", None)

    if driver is None or not is_driver_alive(driver):
        driver = init_selenium(headless=headless)
        _thread_local.driver = driver
        _driver_pool.append(driver)
    return driver
