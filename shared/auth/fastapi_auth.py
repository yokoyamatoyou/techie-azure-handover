# -*- coding: utf-8 -*-
"""FastAPI 依存関係: JWT 認証 + テナント注入

Usage:
    from shared.auth.fastapi_auth import require_auth, get_current_tenant

    @app.get("/api/data")
    async def get_data(user=Depends(require_auth)):
        tenant_id = user["tenant_id"]
        ...
"""
import logging
import os
from typing import Dict

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_validator import AuthError, extract_user_info, verify_token
from .identity_resolver import (
    IdentityLinkRequired,
    IdentityResolutionError,
    IdentityResolverUnavailable,
    resolve_user_info,
)

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# 開発モードフラグ — テスト時にトークン検証をスキップ
_DEV_TENANT_ID = os.environ.get("DEV_TENANT_ID", "dev-tenant-00000000")


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _environment_name() -> str:
    return (
        os.environ.get("ENVIRONMENT")
        or os.environ.get("ASPNETCORE_ENVIRONMENT")
        or os.environ.get("CONTAINER_ENV")
        or ""
    ).strip().lower()


def _dev_mode_enabled() -> bool:
    if not _truthy(os.environ.get("AUTH_DEV_MODE")):
        return False
    if _environment_name() in {"prod", "production"}:
        return _truthy(os.environ.get("ALLOW_AUTH_DEV_MODE_IN_PUBLIC"))
    return True


async def require_verified_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> Dict[str, str]:
    """Verify an Entra token without resolving a canonical TECHIE tenant.

    This dependency is reserved for the second, freshly authenticated token
    used to complete an explicit account-linking ceremony.
    """
    if _dev_mode_enabled():
        return {
            "user_id": "dev-user",
            "email": "dev@localhost",
            "name": "Developer",
            "tenant_id": _DEV_TENANT_ID,
            "legacy_tenant_id": _DEV_TENANT_ID,
            "roles": "admin",
            "identity_status": "dev",
        }

    if not credentials:
        raise HTTPException(status_code=401, detail="認証トークンが必要です")

    try:
        claims = verify_token(credentials.credentials)
        return extract_user_info(claims)
    except AuthError as exc:
        logger.warning("Auth failed: %s", exc)
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        logger.error("Token verification error: %s", exc, exc_info=True)
        raise HTTPException(status_code=401, detail="トークン検証に失敗しました")


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> Dict[str, str]:
    """Verify Entra JWT and resolve the canonical TECHIE tenant."""
    raw_user = await require_verified_identity(request, credentials)
    if _dev_mode_enabled():
        user = raw_user
    else:
        try:
            user = resolve_user_info(raw_user)
        except IdentityResolverUnavailable as exc:
            raise HTTPException(status_code=503, detail={"code": exc.code, "message": str(exc)})
        except IdentityLinkRequired as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "message": str(exc)})
        except IdentityResolutionError as exc:
            raise HTTPException(status_code=403, detail={"code": exc.code, "message": str(exc)})

    # tenant_id をリクエスト state に保存（DB RLS 用）
    request.state.tenant_id = user["tenant_id"]
    request.state.user_id = user["user_id"]
    request.state.principal_id = user.get("principal_id", "")
    request.state.identity_binding_id = user.get("identity_binding_id", "")
    request.state.identity_status = user.get("identity_status", "")
    return user


async def get_current_tenant(request: Request) -> str:
    """リクエストからテナント ID を取得"""
    return getattr(request.state, "tenant_id", _DEV_TENANT_ID if _dev_mode_enabled() else "")
