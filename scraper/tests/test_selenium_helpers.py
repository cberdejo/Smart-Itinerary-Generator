# tests/test_selenium.py
import threading
import pytest
from unittest.mock import patch, MagicMock, call
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from helpers import selenium as mod_selenium


def test_is_driver_alive_handles_missing_session(mock_selenium_driver_no_session):
    assert mod_selenium.is_driver_alive(mock_selenium_driver_no_session) is False


def test_is_driver_alive_handles_invalid_service(mock_selenium_driver):
    mock_selenium_driver.service.is_connectable.return_value = False
    assert mod_selenium.is_driver_alive(mock_selenium_driver) is False


def test_is_driver_alive_returns_true_for_valid_driver(mock_selenium_driver):
    assert mod_selenium.is_driver_alive(mock_selenium_driver) is True


def test_is_driver_alive_handles_exception(mock_selenium_driver):
    mock_selenium_driver.service.is_connectable.side_effect = Exception("Error")
    assert mod_selenium.is_driver_alive(mock_selenium_driver) is False


def test_get_driver_creates_new_driver_when_none_exists():
    with (
        patch.object(mod_selenium, "init_selenium") as mock_init,
        patch.object(mod_selenium, "is_driver_alive", return_value=False),
    ):
        # First call - no driver exists
        driver = mod_selenium.get_driver()

        mock_init.assert_called_once_with(headless=True)
        assert driver == mock_init.return_value


def test_get_driver_reuses_existing_driver(mock_selenium_driver):
    if hasattr(mod_selenium._thread_local, "driver"):
        delattr(mod_selenium._thread_local, "driver")

    with (
        patch.object(
            mod_selenium, "init_selenium", return_value=mock_selenium_driver
        ) as mock_init,
        patch.object(mod_selenium, "is_driver_alive", return_value=True),
    ):
        first_driver = mod_selenium.get_driver()
        second_driver = mod_selenium.get_driver()

        assert first_driver is second_driver
        mock_init.assert_called_once_with(headless=True)


def test_thread_local_driver_storage():
    def get_driver_in_thread(result_list):
        driver = mod_selenium.get_driver()
        result_list.append(driver)

    # Create two threads
    results1 = []
    results2 = []

    thread1 = threading.Thread(target=get_driver_in_thread, args=(results1,))
    thread2 = threading.Thread(target=get_driver_in_thread, args=(results2,))

    with patch.object(
        mod_selenium, "init_selenium", side_effect=[MagicMock(), MagicMock()]
    ):
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

    # Verify each thread got its own driver instance
    assert len(results1) == 1
    assert len(results2) == 1
    assert results1[0] is not results2[0]


def test_get_driver_creates_new_driver_when_existing_is_dead():
    dead_driver = MagicMock()
    new_driver = MagicMock()

    # clean existing driver
    if hasattr(mod_selenium._thread_local, "driver"):
        delattr(mod_selenium._thread_local, "driver")

    with (
        patch.object(
            mod_selenium, "init_selenium", side_effect=[dead_driver, new_driver]
        ) as mock_init,
        patch.object(mod_selenium, "is_driver_alive", side_effect=[False, True]),
    ):
        first_driver = mod_selenium.get_driver()
        second_driver = mod_selenium.get_driver()

        assert first_driver is dead_driver
        assert second_driver is new_driver
        assert mock_init.call_count == 2
