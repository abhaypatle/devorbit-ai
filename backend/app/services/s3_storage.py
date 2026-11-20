import asyncio
import mimetypes
import re
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import boto3

from app.core.config import get_settings


_UNSAFE_KEY_PART = re.compile(r"[^A-Za-z0-9._-]+")
_MEMORY_OBJECTS: dict[str, tuple[bytes, str]] = {}


def _safe_segment(value: str) -> str:
    segment = _UNSAFE_KEY_PART.sub("-", value).strip(".-")
    if not segment or segment in {".", ".."}:
        raise ValueError("Object key segment is empty or invalid")
    return segment[:180]


class S3CompatibleStorage:
    """Non-blocking facade for S3, filesystem, and process-local development storage."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None

    def build_key(self, org_id: str, project_id: str, document_id: str, filename: str) -> str:
        return "/".join(
            (
                _safe_segment(org_id),
                _safe_segment(project_id),
                _safe_segment(document_id),
                _safe_segment(PurePosixPath(filename.replace("\\", "/")).name),
            )
        )

    async def upload(
        self,
        key: str,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> str:
        normalized_key = self._normalize_key(key)
        detected_type = content_type or mimetypes.guess_type(normalized_key)[0] or "application/octet-stream"
        mode = self.settings.storage_mode
        if mode == "memory":
            _MEMORY_OBJECTS[normalized_key] = (content, detected_type)
        elif mode == "filesystem":
            await asyncio.to_thread(self._write_file, normalized_key, content)
        else:
            await asyncio.to_thread(
                self._call_s3,
                "put_object",
                Bucket=self.settings.s3_bucket,
                Key=normalized_key,
                Body=content,
                ContentType=detected_type,
            )
        return normalized_key

    async def read(self, key: str) -> bytes:
        normalized_key = self._normalize_key(key)
        mode = self.settings.storage_mode
        if mode == "memory":
            try:
                return _MEMORY_OBJECTS[normalized_key][0]
            except KeyError:
                raise FileNotFoundError(f"Object {normalized_key!r} was not found") from None
        if mode == "filesystem":
            return await asyncio.to_thread(self._read_file, normalized_key)
        response: dict[str, Any] = await asyncio.to_thread(
            self._call_s3,
            "get_object",
            Bucket=self.settings.s3_bucket,
            Key=normalized_key,
        )
        return await asyncio.to_thread(response["Body"].read)

    async def delete(self, key: str) -> None:
        normalized_key = self._normalize_key(key)
        mode = self.settings.storage_mode
        if mode == "memory":
            _MEMORY_OBJECTS.pop(normalized_key, None)
        elif mode == "filesystem":
            await asyncio.to_thread(self._delete_file, normalized_key)
        else:
            await asyncio.to_thread(
                self._call_s3,
                "delete_object",
                Bucket=self.settings.s3_bucket,
                Key=normalized_key,
            )

    async def download_reference(self, key: str) -> str:
        normalized_key = self._normalize_key(key)
        if self.settings.storage_mode == "s3":
            return await asyncio.to_thread(
                self._call_s3,
                "generate_presigned_url",
                "get_object",
                Params={"Bucket": self.settings.s3_bucket, "Key": normalized_key},
                ExpiresIn=self.settings.s3_presigned_url_ttl_seconds,
            )
        return f"storage://{quote(normalized_key, safe='/')}"

    @staticmethod
    def _normalize_key(key: str) -> str:
        path = PurePosixPath(key)
        if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("Object key must be a relative path without traversal segments")
        return path.as_posix()

    def _s3_client(self):
        if self._client is not None:
            return self._client
        options: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self.settings.s3_region,
        }
        if self.settings.s3_endpoint_url:
            options["endpoint_url"] = self.settings.s3_endpoint_url
        if self.settings.s3_access_key_id:
            options["aws_access_key_id"] = self.settings.s3_access_key_id
        if self.settings.s3_secret_access_key:
            options["aws_secret_access_key"] = self.settings.s3_secret_access_key
        self._client = boto3.client(**options)
        return self._client

    def _call_s3(self, method: str, *args: Any, **kwargs: Any) -> Any:
        return getattr(self._s3_client(), method)(*args, **kwargs)

    def _local_path(self, key: str) -> Path:
        root = Path(self.settings.local_storage_path).resolve()
        destination = (root / Path(*PurePosixPath(key).parts)).resolve()
        if destination != root and root not in destination.parents:
            raise ValueError("Object key escapes local storage directory")
        return destination

    def _write_file(self, key: str, content: bytes) -> None:
        destination = self._local_path(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def _read_file(self, key: str) -> bytes:
        return self._local_path(key).read_bytes()

    def _delete_file(self, key: str) -> None:
        path = self._local_path(key)
        if path.exists():
            path.unlink()


storage = S3CompatibleStorage()
