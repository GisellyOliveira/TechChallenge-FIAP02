"""Adaptador do Cloud Storage: só o necessário para medir o volume do Bronze (FinOps)."""

from __future__ import annotations

from google.cloud import storage


def bucket_size_bytes(project_id: str, bucket: str) -> int:
    client = storage.Client(project=project_id)
    return sum(int(blob.size or 0) for blob in client.list_blobs(bucket))
