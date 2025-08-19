from helpers import minio as mod_minio
from conftest import temp_attr


def test_setup_minio_buckets_creates_when_missing(
    fake_minio_class, fake_minio_settings, monkeypatch
):
    """
    setup_minio_buckets should create the bucket if it does not exist.
    """
    # Patch the Minio class used by helpers.minio and the settings object
    monkeypatch.setattr(mod_minio, "Minio", fake_minio_class)
    monkeypatch.setattr(mod_minio, "settings", fake_minio_settings)

    # Build a client the same way production code does
    client = mod_minio.get_minio()

    # Simulate missing bucket
    client.bucket_exists.return_value = False

    # Act
    mod_minio.setup_minio_buckets(client)

    # Assert
    bucket_name = getattr(mod_minio, "BUCKET", "reports")
    client.make_bucket.assert_called_once_with(bucket_name)
    assert client.created == [bucket_name]


def test_setup_minio_buckets_skips_existing(
    fake_minio_class, fake_minio_settings, monkeypatch
):
    """
    setup_minio_buckets should NOT create the bucket if it already exists.
    """
    # Patch dependencies
    monkeypatch.setattr(mod_minio, "Minio", fake_minio_class)
    monkeypatch.setattr(mod_minio, "settings", fake_minio_settings)

    # Build a client
    client = mod_minio.get_minio()

    # Simulate existing bucket
    client.bucket_exists.return_value = True

    # Act
    mod_minio.setup_minio_buckets(client)

    # Assert
    client.make_bucket.assert_not_called()
    assert client.created == []
