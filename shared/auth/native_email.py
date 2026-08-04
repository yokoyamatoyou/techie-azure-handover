# -*- coding: utf-8 -*-
"""Fail-closed Entra External ID native Email OTP broker.

The browser never receives an Entra continuation token.  Flow state is kept in
an authenticated, encrypted, short-lived envelope.  The broker never selects a
TECHIE business tenant and never reads or writes billing/customer records.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .jwt_validator import AuthError, configured_external_directory_id, verify_token


router = APIRouter(prefix="/api/auth/native-email", tags=["native-email-auth"])

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_SUBDOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_SAFE_UPSTREAM_ERRORS = {
    "attributes_required",
    "credential_required",
    "expired_token",
    "invalid_client",
    "invalid_grant",
    "invalid_request",
    "unauthorized_client",
    "unsupported_challenge_type",
    "user_not_found",
}


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


@dataclass(frozen=True)
class NativeEmailSettings:
    enabled: bool
    tenant_subdomain: str
    client_id: str
    session_key: bytes
    allowed_origins: frozenset[str]
    flow_ttl_seconds: int = 300
    request_timeout_seconds: float = 8.0
    rate_limit_attempts: int = 5
    rate_limit_window_seconds: int = 600

    @classmethod
    def from_env(cls) -> "NativeEmailSettings":
        enabled = _truthy(os.environ.get("EMAIL_NATIVE_AUTH_ENABLED"))
        tenant_subdomain = str(os.environ.get("ENTRA_NATIVE_TENANT_SUBDOMAIN") or "").strip().lower()
        client_id = str(os.environ.get("ENTRA_CLIENT_ID") or "").strip()
        raw_key = str(os.environ.get("EMAIL_NATIVE_AUTH_SESSION_KEY") or "").strip()
        try:
            session_key = _b64url_decode(raw_key) if raw_key else b""
        except Exception:
            session_key = b""
        configured_origins = {
            str(value or "").strip().rstrip("/")
            for value in (
                os.environ.get("HUB_BASE_URL"),
                os.environ.get("HUB_URL"),
                *(os.environ.get("NATIVE_AUTH_ALLOWED_ORIGINS") or "").split(","),
            )
            if str(value or "").strip()
        }
        return cls(
            enabled=enabled,
            tenant_subdomain=tenant_subdomain,
            client_id=client_id,
            session_key=session_key,
            allowed_origins=frozenset(configured_origins),
        )

    @property
    def ready(self) -> bool:
        return bool(
            self.enabled
            and _SUBDOMAIN_RE.fullmatch(self.tenant_subdomain)
            and self.client_id
            and len(self.session_key) == 32
            and self.allowed_origins
        )

    @property
    def base_url(self) -> str:
        subdomain = self.tenant_subdomain
        return f"https://{subdomain}.ciamlogin.com/{subdomain}.onmicrosoft.com"


class NativeEmailStartRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    intent: str = Field(pattern="^(login|signup)$")
    display_name: str = Field(default="", max_length=128)


class NativeEmailVerifyRequest(BaseModel):
    flow_token: str = Field(min_length=32, max_length=16384)
    code: str = Field(min_length=4, max_length=12)


class NativeEmailFlowError(RuntimeError):
    def __init__(self, code: str, status_code: int = 409):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class _FlowSealer:
    _AAD = b"techie-native-email-flow-v1"

    def __init__(self, key: bytes, *, now: Callable[[], float] = time.time):
        if len(key) != 32:
            raise ValueError("native auth session key must be exactly 32 bytes")
        self._aes = AESGCM(key)
        self._now = now

    def seal(self, payload: Mapping[str, Any], ttl_seconds: int) -> str:
        body = dict(payload)
        body["exp"] = int(self._now()) + ttl_seconds
        body["jti"] = secrets.token_urlsafe(16)
        nonce = secrets.token_bytes(12)
        plaintext = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return _b64url_encode(nonce + self._aes.encrypt(nonce, plaintext, self._AAD))

    def open(self, token: str) -> dict[str, Any]:
        try:
            packed = _b64url_decode(token)
            if len(packed) < 29:
                raise ValueError("short envelope")
            nonce, ciphertext = packed[:12], packed[12:]
            body = json.loads(self._aes.decrypt(nonce, ciphertext, self._AAD))
            if not isinstance(body, dict) or int(body.get("exp") or 0) < int(self._now()):
                raise ValueError("expired envelope")
            return body
        except Exception as exc:
            raise NativeEmailFlowError("native_flow_invalid", 410) from exc


class _RateLimiter:
    """Small per-instance abuse shield; platform rate limiting remains required."""

    def __init__(self, attempts: int, window_seconds: int, *, now: Callable[[], float] = time.time):
        self._attempts = attempts
        self._window = window_seconds
        self._now = now
        self._events: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def consume(self, key: str) -> bool:
        now = self._now()
        cutoff = now - self._window
        with self._lock:
            recent = [value for value in self._events.get(key, []) if value > cutoff]
            if len(recent) >= self._attempts:
                self._events[key] = recent
                return False
            recent.append(now)
            self._events[key] = recent
            return True


class NativeEmailBroker:
    def __init__(
        self,
        settings: NativeEmailSettings,
        *,
        post: Callable[..., Any] = requests.post,
        token_verifier: Callable[[str], Mapping[str, Any]] = verify_token,
        directory_id_getter: Callable[[], str] = configured_external_directory_id,
        now: Callable[[], float] = time.time,
    ):
        self.settings = settings
        self._post_request = post
        self._token_verifier = token_verifier
        self._directory_id_getter = directory_id_getter
        self._sealer = _FlowSealer(settings.session_key, now=now) if settings.ready else None
        self._limiter = _RateLimiter(
            settings.rate_limit_attempts,
            settings.rate_limit_window_seconds,
            now=now,
        )

    def require_ready(self) -> None:
        if not self.settings.ready or self._sealer is None:
            raise NativeEmailFlowError("native_auth_unavailable", 503)

    def require_origin(self, origin: str) -> None:
        normalized = str(origin or "").strip().rstrip("/")
        if not normalized or normalized not in self.settings.allowed_origins:
            raise NativeEmailFlowError("native_auth_origin_denied", 403)

    def _rate_key(self, client_key: str, email: str) -> str:
        material = f"{client_key}|{email.lower()}".encode("utf-8")
        return hmac.new(self.settings.session_key, material, hashlib.sha256).hexdigest()

    def _post(self, path: str, data: Mapping[str, str], *, allow_error: bool = False) -> tuple[int, dict[str, Any]]:
        try:
            response = self._post_request(
                f"{self.settings.base_url}{path}",
                data=dict(data),
                timeout=self.settings.request_timeout_seconds,
                allow_redirects=False,
            )
            status = int(response.status_code)
            payload = response.json()
            if not isinstance(payload, dict):
                payload = {}
        except requests.RequestException as exc:
            raise NativeEmailFlowError("native_auth_upstream_unavailable", 503) from exc
        except Exception as exc:
            raise NativeEmailFlowError("native_auth_invalid_response", 502) from exc
        if status >= 400 and not allow_error:
            upstream = str(payload.get("error") or "")
            safe = upstream if upstream in _SAFE_UPSTREAM_ERRORS else "native_auth_rejected"
            if safe in {"invalid_client", "unauthorized_client"}:
                raise NativeEmailFlowError("native_auth_misconfigured", 503)
            if safe in {"expired_token"}:
                raise NativeEmailFlowError("native_flow_expired", 410)
            raise NativeEmailFlowError("native_auth_could_not_continue", 400)
        return status, payload

    def start(self, *, email: str, intent: str, display_name: str, client_key: str) -> dict[str, Any]:
        self.require_ready()
        normalized_email = str(email or "").strip().lower()
        normalized_name = " ".join(str(display_name or "").split())
        if not _EMAIL_RE.fullmatch(normalized_email):
            raise NativeEmailFlowError("email_invalid", 400)
        if intent not in {"login", "signup"}:
            raise NativeEmailFlowError("native_intent_invalid", 400)
        if intent == "signup" and not normalized_name:
            raise NativeEmailFlowError("display_name_required", 400)
        if not self._limiter.consume(self._rate_key(client_key, normalized_email)):
            raise NativeEmailFlowError("native_auth_rate_limited", 429)

        common = {
            "client_id": self.settings.client_id,
            "challenge_type": "oob redirect",
            "username": normalized_email,
        }
        if intent == "signup":
            common["attributes"] = json.dumps({"displayName": normalized_name}, separators=(",", ":"))
            start_path = "/signup/v1.0/start"
            challenge_path = "/signup/v1.0/challenge"
        else:
            start_path = "/oauth2/v2.0/initiate"
            challenge_path = "/oauth2/v2.0/challenge"

        _, started = self._post(start_path, common)
        if str(started.get("challenge_type") or "") == "redirect":
            raise NativeEmailFlowError("native_auth_fallback_required", 409)
        continuation = str(started.get("continuation_token") or "")
        if not continuation:
            raise NativeEmailFlowError("native_auth_invalid_response", 502)
        _, challenged = self._post(
            challenge_path,
            {
                "client_id": self.settings.client_id,
                "challenge_type": "oob redirect",
                "continuation_token": continuation,
            },
        )
        if (
            str(challenged.get("challenge_type") or "") != "oob"
            or str(challenged.get("challenge_channel") or "") != "email"
        ):
            raise NativeEmailFlowError("native_auth_fallback_required", 409)
        next_continuation = str(challenged.get("continuation_token") or "")
        code_length = int(challenged.get("code_length") or 0)
        if not next_continuation or code_length < 4 or code_length > 12:
            raise NativeEmailFlowError("native_auth_invalid_response", 502)
        flow_token = self._sealer.seal(
            {
                "intent": intent,
                "email": normalized_email,
                "continuation_token": next_continuation,
                "code_length": code_length,
            },
            self.settings.flow_ttl_seconds,
        )
        return {
            "flow_token": flow_token,
            "code_length": code_length,
            "challenge_target_label": str(challenged.get("challenge_target_label") or ""),
            "expires_in": self.settings.flow_ttl_seconds,
        }

    def verify(self, *, flow_token: str, code: str) -> dict[str, Any]:
        self.require_ready()
        flow = self._sealer.open(flow_token)
        normalized_code = str(code or "").strip()
        if not normalized_code.isdigit() or len(normalized_code) != int(flow.get("code_length") or 0):
            raise NativeEmailFlowError("otp_invalid", 400)
        continuation = str(flow.get("continuation_token") or "")
        intent = str(flow.get("intent") or "")
        email = str(flow.get("email") or "")
        if not continuation or intent not in {"login", "signup"} or not _EMAIL_RE.fullmatch(email):
            raise NativeEmailFlowError("native_flow_invalid", 410)

        if intent == "signup":
            status, continued = self._post(
                "/signup/v1.0/continue",
                {
                    "client_id": self.settings.client_id,
                    "continuation_token": continuation,
                    "grant_type": "oob",
                    "oob": normalized_code,
                },
                allow_error=True,
            )
            if status >= 400:
                if str(continued.get("error") or "") == "attributes_required":
                    raise NativeEmailFlowError("native_signup_attributes_not_supported", 409)
                raise NativeEmailFlowError("otp_invalid_or_expired", 400)
            continuation = str(continued.get("continuation_token") or "")
            token_data = {
                "client_id": self.settings.client_id,
                "continuation_token": continuation,
                "grant_type": "continuation_token",
                "username": email,
                "scope": "openid profile email",
            }
        else:
            token_data = {
                "client_id": self.settings.client_id,
                "continuation_token": continuation,
                "grant_type": "oob",
                "oob": normalized_code,
                "scope": "openid profile email",
            }

        _, tokens = self._post("/oauth2/v2.0/token", token_data)
        id_token = str(tokens.get("id_token") or "")
        if not id_token:
            raise NativeEmailFlowError("native_auth_token_missing", 502)
        try:
            claims = self._token_verifier(id_token)
            expected_directory = str(self._directory_id_getter() or "").strip().lower()
            actual_directory = str(claims.get("tid") or "").strip().lower()
            if not expected_directory or actual_directory != expected_directory:
                raise AuthError("native token directory mismatch")
        except AuthError as exc:
            raise NativeEmailFlowError("native_auth_token_rejected", 502) from exc
        except Exception as exc:
            raise NativeEmailFlowError("native_auth_token_rejected", 502) from exc
        return {
            "id_token": id_token,
            "expires_in": min(max(int(tokens.get("expires_in") or 0), 0), 86400),
            "intent": intent,
        }


_broker: NativeEmailBroker | None = None
_broker_lock = threading.Lock()


def _get_broker() -> NativeEmailBroker:
    global _broker
    if _broker is None:
        with _broker_lock:
            if _broker is None:
                _broker = NativeEmailBroker(NativeEmailSettings.from_env())
    return _broker


def _client_key(request: Request) -> str:
    return str(request.client.host if request.client else "unknown")


def _raise_http(exc: NativeEmailFlowError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code},
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


def _set_no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.get("/status")
async def native_email_status() -> dict[str, bool]:
    settings = _get_broker().settings
    return {"enabled": settings.enabled, "ready": settings.ready}


@router.post("/start")
async def native_email_start(
    payload: NativeEmailStartRequest,
    request: Request,
    response: Response,
) -> dict[str, Any]:
    broker = _get_broker()
    try:
        _set_no_store(response)
        broker.require_origin(request.headers.get("origin", ""))
        return broker.start(
            email=payload.email,
            intent=payload.intent,
            display_name=payload.display_name,
            client_key=_client_key(request),
        )
    except NativeEmailFlowError as exc:
        _raise_http(exc)


@router.post("/verify")
async def native_email_verify(
    payload: NativeEmailVerifyRequest,
    request: Request,
    response: Response,
) -> dict[str, Any]:
    broker = _get_broker()
    try:
        _set_no_store(response)
        broker.require_origin(request.headers.get("origin", ""))
        return broker.verify(flow_token=payload.flow_token, code=payload.code)
    except NativeEmailFlowError as exc:
        _raise_http(exc)
