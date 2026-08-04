# -*- coding: utf-8 -*-
"""Explicit dual-authentication account-linking API."""
from __future__ import annotations

import hashlib
import os
import secrets
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .fastapi_auth import require_auth, require_verified_identity
from .identity_resolver import RecentAuthenticationRequired, require_recent_authentication
from .jwt_validator import AuthError, configured_external_directory_id

router = APIRouter(prefix="/api/identity", tags=["identity-linking"])

_ALLOWED_PROVIDERS = {"email", "google"}
_LINKABLE_STATUSES = {
    "bound",
    "legacy_bootstrap",
    "provisioned",
    "entra_extension_binding",
    "entra_extension_bootstrap",
}


def _repository():
    # Import lazily so JWT verification and static/offline tests do not require
    # the PostgreSQL driver before an identity DB operation is requested.
    from shared.billing import repository

    return repository


def _identity_linking_enabled() -> bool:
    return str(os.environ.get("IDENTITY_LINKING_ENABLED") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _require_identity_linking_enabled() -> None:
    if not _identity_linking_enabled():
        raise HTTPException(
            status_code=503,
            detail={"code": "identity_linking_unavailable", "message": "identity linking is not enabled"},
        )


class LinkIntentRequest(BaseModel):
    provider: str


class LinkCompleteRequest(BaseModel):
    state: str


def _state_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_fresh(user: Dict[str, Any]) -> None:
    try:
        require_recent_authentication(user)
    except RecentAuthenticationRequired as exc:
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": str(exc)})


def _require_external_directory(user: Dict[str, Any]) -> None:
    try:
        expected = configured_external_directory_id()
    except AuthError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "external_directory_misconfigured", "message": str(exc)},
        )
    actual = str(user.get("directory_tenant_id") or "").strip().lower()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "external_directory_not_configured",
                "message": "TECHIE External ID directory is not configured",
            },
        )
    if actual != expected:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "external_directory_mismatch",
                "message": "identity is not from the TECHIE External ID directory",
            },
        )


@router.get("/bindings")
async def identity_bindings(user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    principal_id = str(user.get("principal_id") or "")
    if not principal_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "canonical_identity_required", "message": "identity resolver cutover is not active"},
        )
    rows = _repository().list_identity_bindings_for_principal(principal_id)
    return {
        "identity_status": user.get("identity_status", ""),
        "bindings": [
            {
                "provider": row.get("identity_provider") or "unknown",
                "status": row.get("status") or "unknown",
                "link_method": row.get("link_method") or "unknown",
                "linked_at": row.get("linked_at"),
            }
            for row in rows
        ],
    }


@router.post("/link-intents")
async def create_link_intent(
    payload: LinkIntentRequest,
    user: Dict[str, Any] = Depends(require_auth),
) -> Dict[str, Any]:
    _require_identity_linking_enabled()
    provider = str(payload.provider or "").strip().lower()
    if provider not in _ALLOWED_PROVIDERS:
        raise HTTPException(status_code=400, detail="provider must be email or google")
    if user.get("identity_status") not in _LINKABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail={"code": "canonical_identity_required", "message": "canonical identity binding is required"},
        )
    _require_fresh(user)
    principal_id = str(user.get("principal_id") or "")
    binding_id = str(user.get("identity_binding_id") or "")
    if not principal_id or not binding_id:
        raise HTTPException(status_code=409, detail="active source identity binding is required")

    state = secrets.token_urlsafe(32)
    _repository().create_identity_link_intent(
        principal_id=principal_id,
        source_identity_binding_id=binding_id,
        state_digest=_state_digest(state),
        requested_provider=provider,
        expires_in_seconds=600,
    )
    return {"state": state, "provider": provider, "expires_in": 600}


@router.post("/link-complete")
async def complete_link(
    payload: LinkCompleteRequest,
    user: Dict[str, Any] = Depends(require_verified_identity),
) -> Dict[str, Any]:
    _require_identity_linking_enabled()
    state = str(payload.state or "").strip()
    if len(state) < 32 or len(state) > 256:
        raise HTTPException(status_code=400, detail="invalid identity-link state")
    _require_fresh(user)
    _require_external_directory(user)
    result = _repository().complete_identity_link(
        state_digest=_state_digest(state),
        token_issuer=str(user.get("token_issuer") or ""),
        directory_tenant_id=str(user.get("directory_tenant_id") or ""),
        subject_type=str(user.get("identity_key_type") or ""),
        subject_value=str(user.get("identity_key") or ""),
        entra_object_id=str(user.get("entra_object_id") or ""),
        token_subject=str(user.get("token_subject") or ""),
        identity_provider=str(user.get("identity_provider") or "unknown"),
        email=str(user.get("email") or ""),
    )
    status = str(result.get("status") or "")
    if status == "completed":
        return {"status": "completed"}
    if status == "conflict":
        raise HTTPException(
            status_code=409,
            detail={"code": "identity_already_linked", "message": "identity is linked to another principal"},
        )
    if status == "provider_mismatch":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "identity_provider_mismatch",
                "message": "selected login method did not match the reauthenticated identity",
            },
        )
    if status == "directory_mismatch":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "identity_directory_mismatch",
                "message": "stored identity directory did not match the verified External ID directory",
            },
        )
    if status == "same_identity":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "identity_same_as_source",
                "message": "the additional login must be different from the source identity",
            },
        )
    if status == "already_used":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "identity_link_state_already_used",
                "message": "identity-link state was already used by a different identity",
            },
        )
    if status == "expired":
        raise HTTPException(status_code=410, detail="identity-link state expired")
    raise HTTPException(status_code=400, detail="identity-link state is invalid or unavailable")
