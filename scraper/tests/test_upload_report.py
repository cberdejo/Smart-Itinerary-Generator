# tests/test_save_task_metadata.py
"""
Tests for `pipeline.tasks.upload_report.save_task_metadata_to_minio`.

- Covers JSON serialization helper (`json_serial`).
- Validates that task metadata is collected, serialized, and uploaded to MinIO.
- Ensures optional/missing fields are handled gracefully.

This version uses the unified fixtures from conftest.py:
- fake_context(flow_run_id) to patch Prefect's get_run_context
- patch_minio to inject FakeMinio into upload_report and capture put_object calls
"""

import re
import json
import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta
from uuid import UUID

from pipeline.tasks.upload_report import (
    save_task_metadata_to_minio,
    json_serial as json_serial_fn,
)
import pipeline.tasks.upload_report as mod


# ----------------------------------------------------------------------
# Unit tests for json_serial
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        (datetime(2024, 1, 2, 3, 4, 5), "2024-01-02T03:04:05"),
        (timedelta(days=1, hours=2, minutes=3), 1 * 24 * 3600 + 2 * 3600 + 3 * 60),
        (
            UUID("12345678-1234-5678-1234-567812345678"),
            "12345678-1234-5678-1234-567812345678",
        ),
    ],
)
def test_json_serial_success(value, expected):
    """json_serial should correctly serialize datetime, timedelta, and UUID."""
    assert json_serial_fn(value) == expected


def test_json_serial_raises_for_unsupported_type():
    """json_serial should raise TypeError for unsupported types."""

    class X: ...

    with pytest.raises(TypeError):
        json_serial_fn(X())


# ----------------------------------------------------------------------
# Async task tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_task_metadata_to_minio_happy_path(
    monkeypatch, fake_context, patch_minio
):
    """
    Happy path:
    - Fake Prefect client returns two task runs fully populated.
    - MinIO put_object is called once with correct metadata.
    - JSON payload contains expected serialized data.
    """
    # Patch Prefect run context
    fake_context("flow-123")

    # Two fake task runs
    tr1 = SimpleNamespace(
        id="task-1",
        name="extract",
        state=SimpleNamespace(name="Completed"),
        start_time=datetime(2025, 8, 10, 12, 30, 0),
        end_time=datetime(2025, 8, 10, 12, 31, 0),
        total_run_time=60.0,
        estimated_run_time=55.0,
        created=datetime(2025, 8, 10, 12, 29, 50),
        updated=datetime(2025, 8, 10, 12, 31, 1),
        tags=("etl", "daily"),
        flow_run_id="flow-123",
        infrastructure_pid="pid-001",
        retries=0,
    )
    tr2 = SimpleNamespace(
        id="task-2",
        name="transform",
        state=SimpleNamespace(name="Completed"),
        start_time=datetime(2025, 8, 10, 12, 31, 0),
        end_time=datetime(2025, 8, 10, 12, 33, 0),
        total_run_time=120.0,
        estimated_run_time=None,
        created=datetime(2025, 8, 10, 12, 30, 55),
        updated=datetime(2025, 8, 10, 12, 33, 2),
        tags=[],
        flow_run_id="flow-123",
        infrastructure_pid=None,
        retries=1,
    )

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def read_task_runs(self, task_run_filter=None):
            # Ensure a filter is passed (shape isn’t important here)
            assert task_run_filter is not None
            return [tr1, tr2]

    # Patch Prefect client & filter used by the task
    monkeypatch.setattr(mod, "get_client", lambda: FakeClient())
    monkeypatch.setattr(mod, "TaskRunFilter", lambda **kwargs: kwargs)

    # patch_minio is the injected FakeMinio instance (from conftest)
    # Run the task (using .fn() to call the underlying function)
    await save_task_metadata_to_minio.fn()

    # Validate MinIO call (first/only upload)
    assert len(patch_minio.put_calls) == 1
    upload = patch_minio.put_calls[0]

    assert upload["bucket_name"] == mod.BUCKET
    assert upload["content_type"] == "application/json"
    assert re.match(
        r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z/task_metadata\.json$",
        upload["object_name"],
    )

    # Validate JSON payload
    payload = json.loads(upload["data"].decode("utf-8"))
    assert isinstance(payload, list) and len(payload) == 2

    by_id = {item["task_run_id"]: item for item in payload}
    t1, t2 = by_id["task-1"], by_id["task-2"]

    # Check fields for task 1
    assert t1["task_name"] == "extract"
    assert t1["state"] == "Completed"
    assert t1["duration_seconds"] == 60.0
    assert t1["total_run_time_seconds"] == 60.0
    assert t1["estimated_run_time_seconds"] == 55.0
    assert t1["tags"] == ["etl", "daily"]
    assert t1["flow_run_id"] == "flow-123"
    assert t1["infrastructure_pid"] == "pid-001"
    assert t1["retries"] == 0

    # Check fields for task 2
    assert t2["task_name"] == "transform"
    assert t2["state"] == "Completed"
    assert t2["duration_seconds"] == 120.0
    assert t2["total_run_time_seconds"] == 120.0
    assert t2["estimated_run_time_seconds"] is None
    assert t2["tags"] == []
    assert t2["flow_run_id"] == "flow-123"
    assert t2["infrastructure_pid"] is None
    assert t2["retries"] == 1

    # Date fields should be serialized as ISO strings
    for item in (t1, t2):
        for k in ("start_time", "end_time", "created", "updated"):
            assert isinstance(item[k], str) and "T" in item[k]


@pytest.mark.asyncio
async def test_save_task_metadata_handles_missing_times_and_optionals(
    monkeypatch, fake_context, patch_minio
):
    """
    Edge cases:
    - start_time and end_time are missing -> duration_seconds = None.
    - state is None -> "Unknown".
    - tags is None -> [].
    - optional fields (total_run_time, retries, infrastructure_pid) missing.
    """
    fake_context("flow-xyz")

    tr = SimpleNamespace(
        id="task-x",
        name="load",
        state=None,  # -> "Unknown"
        start_time=None,  # -> duration None
        end_time=None,  # -> duration None
        created=datetime(2025, 8, 10, 12, 59, 0),
        updated=datetime(2025, 8, 10, 13, 0, 0),
        tags=None,  # -> []
        flow_run_id="flow-xyz",
        # no infrastructure_pid
        # no retries (defaults to 0)
    )

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def read_task_runs(self, task_run_filter=None):
            return [tr]

    monkeypatch.setattr(mod, "get_client", lambda: FakeClient())
    monkeypatch.setattr(mod, "TaskRunFilter", lambda **kwargs: kwargs)

    await save_task_metadata_to_minio.fn()

    # Validate single upload with correct object name format
    assert len(patch_minio.put_calls) == 1
    upload = patch_minio.put_calls[0]
    assert re.match(
        r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z/task_metadata\.json$",
        upload["object_name"],
    )

    payload = json.loads(upload["data"].decode("utf-8"))
    assert len(payload) == 1
    item = payload[0]

    assert item["task_run_id"] == "task-x"
    assert item["task_name"] == "load"
    assert item["state"] == "Unknown"
    assert item["duration_seconds"] is None
    assert item["total_run_time_seconds"] is None
    assert item["estimated_run_time_seconds"] is None
    assert item["tags"] == []
    assert item["flow_run_id"] == "flow-xyz"
    assert item["infrastructure_pid"] is None
    assert item["retries"] == 0
