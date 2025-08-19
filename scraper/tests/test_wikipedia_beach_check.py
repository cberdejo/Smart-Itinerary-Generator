import types
from textwrap import dedent
import pytest
from pipeline.tasks import wikipedia_beach_check as mod_wiki_beach


def test_get_towns_with_beaches_from_wikipedia_parses_sections(
    monkeypatch, mock_response
):
    """
    Test that the parser correctly extracts towns under Andalusian provinces,
    handles text normalization, and filters non-Andalusian provinces.
    """
    test_html = dedent("""
    <html><body>
      <h2><span id="Málaga">Málaga</span></h2>
      <ul>
        <li><a href="/wiki/Nerja">Nerja</a></li>
        <li><a href="/wiki/Rincón_de_la_Victoria">Rincón de la Victoria</a></li>
        <li><a href="/wiki/Another_Town">Another Town</a> (this is a comment)</li>
      </ul>
      <h2><span id="Cádiz">Cádiz</span></h2>
      <ul>
        <li><a href="/wiki/Tarifa">Tarifa</a></li>
      </ul>
      <h2><span id="Murcia">Murcia</span></h2>
      <ul>
        <li><a href="/wiki/Cartagena">Cartagena</a></li>
      </ul>
      <h2><span id="Empty_Section">Empty Section</span></h2>
      <ul></ul>
    </body></html>
    """)

    monkeypatch.setattr(
        mod_wiki_beach,
        "requests",
        types.SimpleNamespace(
            get=lambda *a, **k: mock_response(html_content=test_html)
        ),
    )

    towns = mod_wiki_beach.get_towns_with_beaches_from_wikipedia.fn()

    # Check expected towns are present (case and accent insensitive)
    expected_towns = {
        "nerja",
        "rincón de la victoria",
        "another town",
        "tarifa",
    }

    # Convert to lowercase for case-insensitive comparison
    lower_towns = [town.lower() for town in towns]

    for expected in expected_towns:
        assert expected in lower_towns

    # Check non-Andalusian towns are excluded
    assert "cartagena" not in lower_towns

    # Check we got the expected number of towns
    assert len(towns) == 4  # Nerja, Rincón, Another Town, Tarifa


def test_handles_http_errors(monkeypatch, mock_response):
    """Test that the function handles HTTP errors gracefully."""
    monkeypatch.setattr(
        mod_wiki_beach,
        "requests",
        types.SimpleNamespace(get=lambda *a, **k: mock_response(status_code=500)),
    )

    towns = mod_wiki_beach.get_towns_with_beaches_from_wikipedia.fn()
    assert towns == []


def test_handles_empty_sections(monkeypatch, mock_response):
    """Test that empty sections don't cause issues."""
    test_html = dedent("""
    <html><body>
      <h2><span id="Málaga">Málaga</span></h2>
      <ul></ul>
      <h2><span id="Cádiz">Cádiz</span></h2>
      <ul>
        <li>Not a link</li>
      </ul>
    </body></html>
    """)

    monkeypatch.setattr(
        mod_wiki_beach,
        "requests",
        types.SimpleNamespace(
            get=lambda *a, **k: mock_response(html_content=test_html)
        ),
    )

    towns = mod_wiki_beach.get_towns_with_beaches_from_wikipedia.fn()
    assert towns == []


def test_handles_duplicate_towns(monkeypatch, mock_response):
    """Test that duplicate towns are handled correctly."""
    test_html = dedent("""
    <html><body>
      <h2><span id="Málaga">Málaga</span></h2>
      <ul>
        <li><a href="/wiki/Nerja">Nerja</a></li>
        <li><a href="/wiki/Nerja">Nerja</a></li>
      </ul>
    </body></html>
    """)

    monkeypatch.setattr(
        mod_wiki_beach,
        "requests",
        types.SimpleNamespace(
            get=lambda *a, **k: mock_response(html_content=test_html)
        ),
    )

    towns = mod_wiki_beach.get_towns_with_beaches_from_wikipedia.fn()
    assert len(towns) == 1
    assert towns[0].lower() == "nerja"
