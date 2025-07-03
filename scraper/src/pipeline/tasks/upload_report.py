from datetime import datetime, timedelta
from uuid import UUID
import json
from io import BytesIO

from prefect import task
from prefect.context import get_run_context
from prefect.client.orchestration import get_client
from prefect.server.schemas.filters import TaskRunFilter


from config.minio import get_minio, setup_minio_buckets, BUCKET


def json_serial(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return obj.total_seconds()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


@task
async def save_task_metadata_to_minio() -> None:
    """
    Save task metadata to MinIO

    """
    # Obtener contexto y client de Prefect

    context = get_run_context()
    flow_run_id = context.task_run.flow_run_id

    task_run_filter = TaskRunFilter(flow_run_id={"any_": [flow_run_id]})

    async with get_client() as client:
        task_runs = await client.read_task_runs(task_run_filter=task_run_filter)

    task_data = []

    for tr in task_runs:
        duration = (
            (tr.end_time - tr.start_time).total_seconds()
            if tr.start_time and tr.end_time
            else None
        )

        task_data.append(
            {
                "task_run_id": str(tr.id),
                "task_name": tr.name,
                "state": tr.state.name if tr.state else "Unknown",
                "start_time": tr.start_time,
                "end_time": tr.end_time,
                "duration_seconds": duration,
                "total_run_time_seconds": getattr(tr, "total_run_time", None),
                "estimated_run_time_seconds": getattr(tr, "estimated_run_time", None),
                "created": tr.created,
                "updated": tr.updated,
                "tags": list(tr.tags) if getattr(tr, "tags", None) else [],
                "flow_run_id": str(tr.flow_run_id),
                "infrastructure_pid": (
                    str(tr.infrastructure_pid)
                    if hasattr(tr, "infrastructure_pid") and tr.infrastructure_pid
                    else None
                ),
                "retries": getattr(tr, "retries", 0),
            }
        )

    # Convertir a JSON con serializador seguro
    json_bytes = json.dumps(
        task_data, indent=2, default=json_serial, ensure_ascii=False
    ).encode("utf-8")

    byte_stream = BytesIO(json_bytes)
    byte_stream.seek(0)

    minio_client = get_minio()
    setup_minio_buckets(minio_client)

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    object_name = f"{timestamp}/task_metadata.json"

    minio_client.put_object(
        bucket_name=BUCKET,
        object_name=object_name,
        data=byte_stream,
        length=len(json_bytes),
        content_type="application/json",
    )
