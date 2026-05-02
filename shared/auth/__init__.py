# -*- coding: utf-8 -*-
"""共通認証モジュール"""
from .fastapi_auth import get_current_tenant, require_auth
from .jwt_validator import AuthError, extract_tenant_id, extract_user_info, verify_token
from .nicegui_auth import NiceGUIAuthMiddleware

__all__ = [
    "AuthError",
    "NiceGUIAuthMiddleware",
    "extract_tenant_id",
    "extract_user_info",
    "get_current_tenant",
    "require_auth",
    "verify_token",
]
