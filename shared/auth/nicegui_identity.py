# -*- coding: utf-8 -*-
"""Helpers to resolve the current authenticated NiceGUI user."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from nicegui import app, ui

from .jwt_validator import AuthError, extract_user_info, verify_token

_DEV_MODE = os.environ.get("AUTH_DEV_MODE", "").lower() in ("1", "true", "yes")
_DEV_TENANT_ID = os.environ.get("DEV_TENANT_ID", "dev-tenant-00000000")


def _extract_token_from_request(request: Any) -> Optional[str]:
    if request is None:
        return None

    headers = getattr(request, "headers", None)
    if headers:
        auth_header = headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()

    cookies = getattr(request, "cookies", None)
    if cookies:
        return cookies.get("access_token")

    return None


def get_current_nicegui_user() -> Dict[str, str]:
    """Resolve the current authenticated user inside NiceGUI event handlers."""
    if _DEV_MODE:
        return {
            "user_id": "dev-user",
            "email": "dev@localhost",
            "name": "Developer",
            "tenant_id": _DEV_TENANT_ID,
            "roles": "admin",
        }

    client = getattr(ui.context, "client", None)
    request = getattr(client, "request", None)
    token = _extract_token_from_request(request)

    storage_user = getattr(app.storage, "user", None)
    if not token and isinstance(storage_user, dict):
        if storage_user.get("tenant_id") and storage_user.get("user_id"):
            return {
                "user_id": str(storage_user.get("user_id", "")),
                "email": str(storage_user.get("email", "")),
                "name": str(storage_user.get("name", "")),
                "tenant_id": str(storage_user.get("tenant_id", "")),
                "roles": str(storage_user.get("roles", "user")),
            }
        token = storage_user.get("access_token")

    if not token:
        raise RuntimeError("Authentication required")

    try:
        claims = verify_token(str(token))
    except AuthError as exc:
        raise RuntimeError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive path
        raise RuntimeError("Token verification failed") from exc

    return extract_user_info(claims)
