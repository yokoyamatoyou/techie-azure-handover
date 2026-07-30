# -*- coding: utf-8 -*-
"""Authentication middleware for public NiceGUI services.

The Hub performs the Entra External ID browser flow. When a user opens a
service from the Hub, the Hub forwards a short-lived token once as a query
parameter. This middleware validates it, stores it as an HttpOnly cookie for
the service host, removes the token from the URL, and protects all subsequent
direct requests.
"""
from __future__ import annotations

import logging
import os
from typing import Optional
from urllib.parse import urlencode

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from .jwt_validator import AuthError, extract_user_info, verify_token

logger = logging.getLogger(__name__)

_DEV_TENANT_ID = os.environ.get("DEV_TENANT_ID", "dev-tenant-00000000")

_PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/healthz",
        "/_nicegui",
        "/static",
        "/assets",
        "/branding",
        "/favicon.ico",
        "/manifest.json",
        "/robots.txt",
        "/flutter_service_worker.js",
        "/login",
        "/callback",
        "/logout",
        "/webhook/stripe",
        "/api/stripe/webhook",
        "/api/stripe/webhooks",
    }
)


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
    """Allow AUTH_DEV_MODE only outside production unless explicitly allowed."""
    if not _truthy(os.environ.get("AUTH_DEV_MODE")):
        return False
    if _environment_name() in {"prod", "production"}:
        return _truthy(os.environ.get("ALLOW_AUTH_DEV_MODE_IN_PUBLIC"))
    return True


def _auth_enforced() -> bool:
    return _truthy(os.environ.get("AUTH_ENFORCE_SERVICES")) or _environment_name() in {"prod", "production"}


def _entitlement_enforced() -> bool:
    return _truthy(os.environ.get("REQUIRE_ACTIVE_ENTITLEMENT")) or _truthy(os.environ.get("AUTH_REQUIRE_ENTITLEMENT"))


def _redirect_pages_without_entitlement() -> bool:
    """Never redirect already-rendered NiceGUI pages for entitlement failures.

    Credit checks are enforced by API endpoints and explicit service actions.
    Redirecting page requests is unsafe for NiceGUI because websocket reconnects
    or page refreshes can happen while a long-running result is still rendering;
    if the last credit is consumed successfully, a redirect would discard the
    result page and make the user think the run failed.
    """
    return False


def _is_public(path: str) -> bool:
    return any(path == public or path.startswith(f"{public}/") for public in _PUBLIC_PATHS)


def _hub_login_url(request: Request) -> str:
    configured = os.environ.get("HUB_LOGIN_URL") or os.environ.get("HUB_BASE_URL") or os.environ.get("HUB_URL") or "/login"
    configured = configured.rstrip("/")
    next_url = str(request.url)
    if configured.startswith("http"):
        return f"{configured}/login?{urlencode({'next': next_url})}" if not configured.endswith("/login") else f"{configured}?{urlencode({'next': next_url})}"
    return f"/login?{urlencode({'next': next_url})}"


def _hub_plans_url(request: Request) -> str:
    configured = os.environ.get("HUB_BASE_URL") or os.environ.get("HUB_URL") or ""
    service_key = os.environ.get("TECHIE_SERVICE_KEY") or os.environ.get("SERVICE_KEY") or ""
    query = {"entitlement": "required", "next": str(request.url)}
    if service_key:
        query["service"] = service_key
    if configured:
        return f"{configured.rstrip('/')}/plans?{urlencode(query)}"
    return f"/plans?{urlencode(query)}"


def _has_active_entitlement(tenant_id: str) -> bool:
    service_key = os.environ.get("TECHIE_SERVICE_KEY") or os.environ.get("SERVICE_KEY") or None
    try:
        from shared.usage.repository import has_active_entitlement

        return has_active_entitlement(tenant_id=tenant_id, service_key=service_key)
    except Exception:
        logger.exception("Failed to verify active entitlement for tenant %s", tenant_id)
        return False


def _allow_zero_credit_page_access(path: str) -> bool:
    """Allow read-only pages that may be opened after spending the final credit."""
    allowed_prefixes = (
        "/runs/",
    )
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in allowed_prefixes)


def _same_url_without_auth_query(request: Request) -> str:
    filtered = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key not in {"access_token", "id_token", "return_to"}
    ]
    query = urlencode(filtered, doseq=True)
    url = request.url.replace(query=query)
    return str(url)


class NiceGUIAuthMiddleware(BaseHTTPMiddleware):
    """Protect NiceGUI/Starlette apps with Entra JWT validation."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        if _is_public(path):
            return await call_next(request)

        if _dev_mode_enabled():
            request.state.tenant_id = _DEV_TENANT_ID
            request.state.user_id = "dev-user"
            request.state.user_email = "dev@localhost"
            request.state.user_name = "Developer"
            request.state.user_roles = "admin"
            return await call_next(request)

        token = _extract_token(request)
        if not token:
            if path.startswith("/api/") or not _auth_enforced():
                return JSONResponse({"detail": "Authentication token is required."}, status_code=401)
            return RedirectResponse(url=_hub_login_url(request), status_code=302)

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
                return JSONResponse({"detail": "Authentication failed."}, status_code=401)
            return RedirectResponse(url=_hub_login_url(request), status_code=302)

        query_token = request.query_params.get("access_token") or request.query_params.get("id_token")
        if query_token:
            response = RedirectResponse(url=_same_url_without_auth_query(request), status_code=302)
            response.set_cookie(
                "access_token",
                token,
                secure=True,
                httponly=True,
                samesite="lax",
                max_age=3600,
            )
            return response

        if _entitlement_enforced():
            entitlement_active = _has_active_entitlement(str(request.state.tenant_id))
            request.state.entitlement_active = entitlement_active
            if not entitlement_active and path.startswith("/api/"):
                return JSONResponse({"detail": "Active subscription or credits are required."}, status_code=402)
            if (
                not entitlement_active
                and _redirect_pages_without_entitlement()
                and not _allow_zero_credit_page_access(path)
            ):
                return RedirectResponse(url=_hub_plans_url(request), status_code=302)

        return await call_next(request)


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    query_token = request.query_params.get("access_token") or request.query_params.get("id_token")
    if query_token:
        return query_token.strip()

    return request.cookies.get("access_token")
