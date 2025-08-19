from pipeline.tasks import save_data as mod_save_data
from unittest.mock import patch
from app_config.db_models import Intangible, Town, RealEstate, Image
from sqlmodel import select
from sqlalchemy import func


def test_chunked_empty_iterable():
    """Test chunked with empty iterable returns no chunks"""
    chunks = list(mod_save_data.chunked([], 10))
    assert len(chunks) == 0


def test_chunked_exact_multiple():
    """Test chunked when iterable length is exact multiple of chunk size"""
    data = list(range(9))
    chunks = list(mod_save_data.chunked(data, 3))
    assert len(chunks) == 3
    assert all(len(chunk) == 3 for chunk in chunks)


def test_chunked_less_than_size():
    """Test chunked when iterable is smaller than chunk size"""
    data = list(range(2))
    chunks = list(mod_save_data.chunked(data, 10))
    assert len(chunks) == 1
    assert len(chunks[0]) == 2


def test_build_upsert_stmt_with_empty_rows():
    """Test upsert statement building with empty rows list"""
    stmt = mod_save_data.build_upsert_stmt(Town, [], conflict_cols=["municipality_ine"])
    assert stmt is not None
    # Should still produce a valid statement even with empty rows


def test_deduplicate_records_empty_input():
    """Test deduplicate_records with empty input"""
    result = mod_save_data.deduplicate_records([], key_func=lambda x: x)
    assert len(result) == 0


def test_deduplicate_records_with_dicts():
    """Test deduplicate_records with dictionary records"""
    records = [
        {"id": 1, "name": "A"},
        {"id": 1, "name": "A"},  # duplicate
        {"id": 2, "name": "B"},
    ]
    deduplicated = mod_save_data.deduplicate_records(
        records, key_func=lambda x: (x["id"], x["name"])
    )
    assert len(deduplicated) == 2
    assert {"id": 1, "name": "A"} in deduplicated
    assert {"id": 2, "name": "B"} in deduplicated


def test_load_info_to_postgres_empty_inputs(sqlite_session):
    """Test load_info_to_postgres with all empty inputs"""
    result = mod_save_data.load_info_to_postgres([], [], [], [])
    assert result == 0

    # Verify no records were inserted
    total_towns = sqlite_session.exec(select(func.count()).select_from(Town)).one()
    total_intangibles = sqlite_session.exec(
        select(func.count()).select_from(Intangible)
    ).one()
    total_real_estate = sqlite_session.exec(
        select(func.count()).select_from(RealEstate)
    ).one()
    total_images = sqlite_session.exec(select(func.count()).select_from(Image)).one()

    assert total_towns == 0
    assert total_intangibles == 0
    assert total_real_estate == 0
    assert total_images == 0


def test_integration_load_info_to_postgres(sqlite_session, sample_town_model):
    with (
        patch("pipeline.tasks.save_data.get_engine", return_value=sqlite_session.bind),
        patch("pipeline.tasks.save_data.get_session", return_value=sqlite_session),
    ):
        towns = sample_town_model(3)

        result = mod_save_data.load_info_to_postgres(towns, [], [], [])
        rows = sqlite_session.exec(select(Town)).all()

        assert result == 0
        assert len(rows) == 3


def test_load_info_to_postgres_with_duplicates(
    sqlite_session, monkeypatch, sample_town_model
):
    """Test that duplicates are properly handled"""
    monkeypatch.setattr(
        "pipeline.tasks.save_data.get_engine", lambda: sqlite_session.bind
    )
    monkeypatch.setattr(
        "pipeline.tasks.save_data.get_session", lambda engine: sqlite_session
    )

    towns = sample_town_model(2)
    # Add duplicates
    towns += sample_town_model(2)
    result = mod_save_data.load_info_to_postgres(towns, [], [], [])
    assert result == 0
    # Should only have 2 unique towns
    total = sqlite_session.exec(select(func.count()).select_from(Town)).one()

    assert total == 2


def test_load_info_to_postgres_error_handling(monkeypatch):
    """Test error handling in load_info_to_postgres"""

    # Mock get_engine to raise an error using monkeypatch
    def mock_get_engine():
        raise Exception("Test error")

    with patch(
        "pipeline.tasks.save_data.get_engine", side_effect=Exception("Test error")
    ):
        result = mod_save_data.load_info_to_postgres([], [], [], [])
        assert result == 0
