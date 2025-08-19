from pipeline.tasks import get_andalusia_towns_ubi_and_name as mod_andalusia
import pytest


def test_get_municipality_name_and_ubi_filters_and_parses(monkeypatch, mock_requests):
    """
    Test the get_municipality_name_and_ubi function when response code is 200.
    mock_requests fixture is used to mock the requests.get function. It returns a json
    with three towns, the first one inside Andalusia, the second one outside, and the
    third one with no coordinates.

    The function should return a list with one town (The one inside Andalusia).

    """

    monkeypatch.setattr(mod_andalusia, "requests", mock_requests)

    result = mod_andalusia.get_municipality_name_and_ubi.fn()

    assert isinstance(result, list)
    assert len(result) == 1

    row = result[0]
    assert row["municipality_name"] == "Ronda"
    assert row["province_identifier"] == 29
    assert row["province_name"] == "Málaga"
    assert isinstance(row["latitude"], float)
    assert isinstance(row["longitude"], float)


def test_get_municipality_name_and_ubi_http_error(monkeypatch, mock_requests_error):
    """
    Test the get_municipality_name_and_ubi function when response code is not 200.
    mock_requests_error fixture is used to mock the requests.get function. It returns
    a BadResponse with status code 500.

    The function should raise an exception.
    """
    monkeypatch.setattr(mod_andalusia, "requests", mock_requests_error)

    with pytest.raises(Exception) as e:
        mod_andalusia.get_municipality_name_and_ubi.fn()

    assert "HTTP Error 500" in str(e.value)
