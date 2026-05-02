# -*- coding: utf-8 -*-
"""NiceGUI 認証ミドルウェア

NiceGUI の app.middleware / app.on_connect で JWT 検証を行い、
セッションにユーザー情報とテナント ID を注入する。
"""
import logging
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from .jwt_validator import AuthError, extract_user_info, verify_token

logger = logging.getLogger(__name__)

_DEV_MODE = os.environ.get("AUTH_DEV_MODE", "").lower() in ("1", "true", "yes")
_DEV_TENANT_ID = os.environ.get("DEV_TENANT_ID", "dev-tenant-00000000")

# 認証不要パス
_PUBLIC_PATHS = frozenset({
    "/health", "/_nicegui", "/static", "/favicon.ico",
    "/login", "/callback", "/logout",
})


def _is_public(path: str) -> bool:
    return any(path.startswith(p) for p in _PUBLIC_PATHS)


class NiceGUIAuthMiddleware(BaseHTTPMiddleware):
    """Starlette ミドルウェアとして NiceGUI アプリに組み込む。

    Usage:
        from shared.auth.nicegui_auth import NiceGUIAuthMiddleware
        from nicegui import app
        app.add_middleware(NiceGUIAuthMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if _is_public(path):
            return await call_next(request)

        if _DEV_MODE:
            request.state.tenant_id = _DEV_TENANT_ID
            request.state.user_id = "dev-user"
            request.state.user_email = "dev@localhost"
            request.state.user_name = "Developer"
            request.state.user_roles = "admin"
            return await call_next(request)

        # Authorization ヘッダーまたはクッキーからトークン取得
        token = _extract_token(request)

        if not token:
            # API リクエストは 401、ブラウザは login リダイレクト
            if path.startswith("/api/"):
                return JSONResponse(
                    {"detail": "認証が必要です"},
                    status_code=401,
                )
            return RedirectResponse(url="/login", status_code=302)

        try:
            claims = verify_token(token)
            user = extract_user_info(claims)
            request.state.tenant_id = user["tenant_id"]
            request.state.user_id = user["user_id"]
            request.state.user_email = user["email"]
            request.state.user_name = user["name"]
            request.state.user_roles = user["roles"]
        except (AuthError, Exception) as exc:
            logger.warning("NiceGUI auth failed for %s: %s", path, exc)
            if path.startswith("/api/"):
                return JSONResponse(
                    {"detail": "認証に失敗しました"},
                    status_code=401,
                )
            return RedirectResponse(url="/login", status_code=302)

        return await call_next(request)


def _extract_token(request: Request) -> Optional[str]:
    """Authorization ヘッダーまたは Cookie からトークンを取得"""
    # 1. Authorization ヘッダー (Bearer token)
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    # 2. Cookie (SPA のリダイレクトフロー後)
    return request.cookies.get("access_token")
