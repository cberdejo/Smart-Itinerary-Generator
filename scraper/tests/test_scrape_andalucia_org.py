# tests/test_scrape_from_turismo_andalucia.py
import pytest
from unittest.mock import patch, MagicMock
from selenium.common.exceptions import WebDriverException, TimeoutException
from pipeline.tasks import scrape_from_turismo_andalucia as mod_scraper
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from tenacity import RetryError


def test_normalize_name_unicode():
    normalize = mod_scraper.normalize_name
    assert normalize("Rincón de la Victoria") == "rincon-de-la-victoria"
    assert normalize("Málaga") == "malaga"
    assert normalize("Córdoba 123!@#") == "cordoba-123"
    assert normalize("San José del Valle") == "san-jose-del-valle"
    assert normalize("") == ""


def test_accept_cookies_no_button_no_crash(mock_selenium_driver):
    mock_selenium_driver.find_element.side_effect = Exception("not found")
    # Should not raise any exception
    mod_scraper.accept_cookies_if_present(mock_selenium_driver)
    mock_selenium_driver.find_element.assert_called_once()


def test_accept_cookies_with_button(mock_selenium_driver):
    mock_button = MagicMock()
    mock_button.is_displayed.return_value = True
    mock_button.is_enabled.return_value = True

    mock_selenium_driver.find_element.return_value = mock_button

    mod_scraper.accept_cookies_if_present(mock_selenium_driver, verbose=True)

    expected_xpath = (
        "//button[@mode='primary' and "
        ".//span[contains(translate(text(),'acepto','ACEPTO'),'ACEPTO')]]"
    )
    mock_selenium_driver.find_element.assert_any_call(By.XPATH, expected_xpath)
    mock_selenium_driver.execute_script.assert_called_once_with(
        "arguments[0].click();", mock_button
    )


@pytest.mark.parametrize(
    "section_name,expected_xpath",
    [
        ("Historia", "//h2[normalize-space()='Historia']/preceding-sibling::p"),
        ("About", "//h2[normalize-space()='About']/preceding-sibling::p"),
    ],
)
def test_get_paragraphs_before_section_h2(
    mock_selenium_driver, section_name, expected_xpath
):
    mock_selenium_driver.find_elements.return_value = [
        MagicMock(text="First paragraph"),
        MagicMock(text="Second paragraph"),
    ]
    result = mod_scraper.get_paragraphs_before_section_h2(
        mock_selenium_driver, section_name
    )
    assert result == "First paragraph\n\nSecond paragraph"
    mock_selenium_driver.find_elements.assert_called_once_with(By.XPATH, expected_xpath)


def test_extract_images(mock_selenium_driver):
    mock_img1 = MagicMock()
    mock_img1.get_attribute.return_value = "http://example.com/img1.jpg"
    mock_img2 = MagicMock()
    mock_img2.get_attribute.return_value = "http://example.com/img2.jpg"

    mock_selenium_driver.find_elements.return_value = [mock_img1, mock_img2]

    images = mod_scraper.extract_images(mock_selenium_driver)
    assert images == ["http://example.com/img1.jpg", "http://example.com/img2.jpg"]

    expected_css = (
        "div.detail-gallery div.slider-cont:not(.slider-thumbnails) picture img"
    )
    mock_selenium_driver.find_elements.assert_called_once_with(
        By.CSS_SELECTOR, expected_css
    )


def test_scrap_tourism_url_success(mock_selenium_driver):
    mock_selenium_driver.get.return_value = None
    mock_selenium_driver.find_element.return_value = MagicMock(text="Test Title")

    with (
        patch.object(mod_scraper, "accept_cookies_if_present"),
        patch.object(
            mod_scraper,
            "get_paragraphs_before_section_h2",
            return_value="Test description",
        ),
        patch.object(
            mod_scraper, "get_paragraphs_after_section_h2", return_value="Test history"
        ),
        patch.object(mod_scraper, "extract_images", return_value=["img1.jpg"]),
    ):
        result = mod_scraper.scrap_tourism_url(mock_selenium_driver, "http://test.com")
        assert result == {
            "description": "Test description",
            "history": "Test history",
            "images": ["img1.jpg"],
        }


def test_scrap_tourism_url_driver_failure(mock_selenium_driver_no_session):
    with pytest.raises(RetryError):
        mod_scraper.scrap_tourism_url(
            mock_selenium_driver_no_session, "http://test.com"
        )


def test_process_batch_no_failures(mock_selenium_driver):
    with (
        patch.object(mod_scraper, "WebDriverWait") as wait_mock,
        patch.object(mod_scraper, "accept_cookies_if_present"),
        patch.object(
            mod_scraper, "get_paragraphs_before_section_h2", return_value="desc ok"
        ),
        patch.object(
            mod_scraper, "get_paragraphs_after_section_h2", return_value="hist ok"
        ),
        patch.object(mod_scraper, "extract_images", return_value=["img1", "img2"]),
    ):
        wait_mock.return_value.until.return_value = True

        result = mod_scraper.scrap_tourism_url(
            mock_selenium_driver,
            "http://test.com",
            verbose=True,
            respect_crawl_delay=False,
        )

    assert mock_selenium_driver.get.call_count == 1
    assert result == {
        "description": "desc ok",
        "history": "hist ok",
        "images": ["img1", "img2"],
    }


def test_scrap_tourism_url_retry_then_success(mock_selenium_driver):
    mock_selenium_driver.get.side_effect = [
        TimeoutException("t1"),
        TimeoutException("t2"),
        None,  # success on third try
    ]
    #  Mock  function
    with (
        patch.object(mod_scraper, "WebDriverWait") as wait_mock,
        patch.object(mod_scraper, "accept_cookies_if_present"),
        patch.object(
            mod_scraper, "get_paragraphs_before_section_h2", return_value="desc ok"
        ),
        patch.object(
            mod_scraper, "get_paragraphs_after_section_h2", return_value="hist ok"
        ),
        patch.object(mod_scraper, "extract_images", return_value=["img1", "img2"]),
    ):
        wait_mock.return_value.until.return_value = True

        result = mod_scraper.scrap_tourism_url(
            mock_selenium_driver,
            "http://test.com",
            verbose=True,
            respect_crawl_delay=False,
        )

    assert mock_selenium_driver.get.call_count == 3
    assert result == {
        "description": "desc ok",
        "history": "hist ok",
        "images": ["img1", "img2"],
    }


def test_process_batch_empty_batch():
    result = mod_scraper.process_batch([], batch_num=1)
    assert result == []
