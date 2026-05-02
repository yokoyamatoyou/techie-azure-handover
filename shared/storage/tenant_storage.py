# -*- coding: utf-8 -*-
"""テナント分離ファイルストレージ

ローカル: ファイルシステムの tenant_id 付きディレクトリ
Azure:   Azure Blob Storage の tenant_id プレフィックス
"""
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")  # "local" | "azure_blob"
AZURE_STORAGE_CONNECTION = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "techie-files")
LOCAL_STORAGE_ROOT = Path(os.environ.get("LOCAL_STORAGE_ROOT", "./data/tenant_files"))


def _validate_path_component(name: str) -> str:
    """パストラバーサル防止"""
    clean = name.replace("..", "").replace("/", "").replace("\\", "").strip()
    if not clean:
        raise ValueError(f"Invalid path component: {name!r}")
    return clean


def get_tenant_path(tenant_id: str, *subpath: str) -> Path:
    """テナント専用ローカルディレクトリのパスを取得"""
    safe_tenant = _validate_path_component(tenant_id)
    tenant_dir = LOCAL_STORAGE_ROOT / safe_tenant
    if subpath:
        safe_parts = [_validate_path_component(p) for p in subpath]
        tenant_dir = tenant_dir.joinpath(*safe_parts)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir


def save_file(
    tenant_id: str,
    category: str,
    filename: str,
    content: bytes,
) -> str:
    """ファイルを保存し、参照パス/URL を返す"""
    safe_tenant = _validate_path_component(tenant_id)
    safe_category = _validate_path_component(category)
    safe_filename = _validate_path_component(filename)

    if STORAGE_BACKEND == "azure_blob" and AZURE_STORAGE_CONNECTION:
        return _save_to_blob(safe_tenant, safe_category, safe_filename, content)

    # ローカルファイルシステム
    dest = get_tenant_path(safe_tenant, safe_category)
    file_path = dest / safe_filename
    file_path.write_bytes(content)
    logger.info("Saved file: %s", file_path)
    return str(file_path)


def _save_to_blob(tenant_id: str, category: str, filename: str, content: bytes) -> str:
    """Azure Blob Storage に保存"""
    from azure.storage.blob import BlobServiceClient

    blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION)
    container_client = blob_service.get_container_client(AZURE_STORAGE_CONTAINER)

    # テナント ID をプレフィックスとして Blob 名を構成
    blob_name = f"{tenant_id}/{category}/{filename}"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(content, overwrite=True)

    logger.info("Uploaded to blob: %s", blob_name)
    return blob_client.url


def read_file(
    tenant_id: str,
    category: str,
    filename: str,
) -> Optional[bytes]:
    """ファイルを読み取り"""
    safe_tenant = _validate_path_component(tenant_id)
    safe_category = _validate_path_component(category)
    safe_filename = _validate_path_component(filename)

    if STORAGE_BACKEND == "azure_blob" and AZURE_STORAGE_CONNECTION:
        return _read_from_blob(safe_tenant, safe_category, safe_filename)

    file_path = get_tenant_path(safe_tenant, safe_category) / safe_filename
    if file_path.exists():
        return file_path.read_bytes()
    return None


def _read_from_blob(tenant_id: str, category: str, filename: str) -> Optional[bytes]:
    """Azure Blob Storage から読み取り"""
    from azure.storage.blob import BlobServiceClient

    blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION)
    container_client = blob_service.get_container_client(AZURE_STORAGE_CONTAINER)
    blob_name = f"{tenant_id}/{category}/{filename}"

    try:
        blob_client = container_client.get_blob_client(blob_name)
        return blob_client.download_blob().readall()
    except Exception:
        return None
