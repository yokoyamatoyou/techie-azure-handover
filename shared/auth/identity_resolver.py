# -*- coding: utf-8 -*-
"""Resolve verified Entra identities to canonical TECHIE principals.

The JWT issuer/object identity remains the authentication evidence. The
canonical principal and business tenant are application authorization and
billing coordinates. Email is only a collision hint and is never an automatic
linking key.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class IdentityResolutionError(RuntimeError):
    """A verified identity cannot be safely mapped to a business tenant."""

    code = "identity_resolution_failed"


class IdentityLinkRequired(IdentityResolutionError):
    """An unbound identity collides with an existing account hint."""

    code = "identity_link_required"


class IdentityResolverUnavailable(IdentityResolutionError):
    """The canonical identity store is unavailable or not migrated."""

    code = "identity_resolver_unavailable"


class RecentAuthenticationRequired(IdentityResolutionError):
    """A sensitive identity-link action needs a fresh provider login."""

    code = "recent_authentication_required"


def identity_resolver_mode() -> str:
    return str(os.environ.get("AUTH_IDENTITY_RESOLVER_MODE", "legacy")).strip().lower()


def identity_auto_provision_enabled() -> bool:
    return str(os.environ.get("AUTH_IDENTITY_AUTO_PROVISION", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def identity_binding_claims_enabled() -> bool:
    """Trust Entra tenant/principal claims only after write controls are audited."""
    return str(os.environ.get("AUTH_TRUST_ENTRA_BINDING_CLAIMS", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _configured_external_directory_id() -> str:
    tenant_id = str(os.environ.get("ENTRA_EXTERNAL_ID_TENANT_ID") or "").strip().lower()
    directory_id = str(os.environ.get("ENTRA_EXTERNAL_ID_DIRECTORY_ID") or "").strip().lower()
    if tenant_id and directory_id and tenant_id != directory_id:
        raise IdentityResolutionError("External ID directory settings conflict")
    return tenant_id or directory_id


def require_recent_authentication(user: Dict[str, Any], *, max_age_seconds: int = 600) -> None:
    """Require a recently issued verified token for identity-link mutations."""
    try:
        issued_at = int(str(user.get("issued_at") or "0"))
    except (TypeError, ValueError):
        issued_at = 0
    now = int(time.time())
    if not issued_at or issued_at > now + 60 or now - issued_at > max_age_seconds:
        raise RecentAuthenticationRequired("本人確認をやり直してからアカウント連携を続けてください")


def _apply_binding(user: Dict[str, Any], binding: Dict[str, Any], *, status: str) -> Dict[str, Any]:
    resolved = dict(user)
    resolved["tenant_id"] = str(binding["tenant_id"])
    resolved["principal_id"] = str(binding["principal_id"])
    resolved["identity_binding_id"] = str(binding["identity_binding_id"])
    resolved["identity_status"] = status
    return resolved


def _observe_shadow_tenant(
    user: Dict[str, Any],
    candidate_tenant_id: Any,
    *,
    source: str,
) -> Dict[str, Any]:
    """Compare a read-only candidate without exposing its coordinates."""
    if source not in {"binding", "legacy"}:
        raise ValueError("unknown shadow observation source")
    shadow = dict(user)
    current_tenant = str(user.get("tenant_id") or "").strip().lower()
    canonical_tenant = str(candidate_tenant_id or "").strip().lower()
    shadow["identity_status"] = (
        f"shadow_{source}_match"
        if current_tenant and canonical_tenant and current_tenant == canonical_tenant
        else f"shadow_{source}_tenant_mismatch"
    )
    shadow["principal_id"] = ""
    shadow["identity_binding_id"] = ""
    logger.info("Identity resolver observation: %s", shadow["identity_status"])
    return shadow


def resolve_user_info(
    user: Dict[str, Any],
    *,
    repository: Optional[Any] = None,
    mode: Optional[str] = None,
    allow_auto_provision: Optional[bool] = None,
) -> Dict[str, Any]:
    """Resolve a verified token user to a canonical principal and tenant.

    Modes:
    - ``legacy``: preserve the existing extension_tenantId/oid/sub behavior.
    - ``shadow``: read an existing binding but never create or enforce one.
    - ``enforce``: require a binding, guarded legacy bootstrap, or approved
      new-account auto-provisioning.
    """
    selected_mode = (mode or identity_resolver_mode()).strip().lower()
    if selected_mode not in {"legacy", "shadow", "enforce"}:
        raise IdentityResolutionError("AUTH_IDENTITY_RESOLVER_MODE is invalid")

    if selected_mode == "legacy":
        legacy = dict(user)
        legacy.setdefault("principal_id", "")
        legacy.setdefault("identity_binding_id", "")
        legacy["identity_status"] = "legacy"
        return legacy

    expected_directory_id = _configured_external_directory_id()
    actual_directory_id = str(user.get("directory_tenant_id") or "").strip().lower()
    if selected_mode == "enforce":
        if not expected_directory_id:
            raise IdentityResolutionError("ENTRA_EXTERNAL_ID_DIRECTORY_ID must be configured before enforce mode")
        if not actual_directory_id or actual_directory_id != expected_directory_id:
            raise IdentityResolutionError("verified identity is not from the TECHIE External ID directory")
    elif expected_directory_id and actual_directory_id != expected_directory_id:
        shadow = dict(user)
        shadow["identity_status"] = "shadow_directory_mismatch"
        return shadow

    issuer = str(user.get("token_issuer") or "").strip().rstrip("/").lower()
    key_type = str(user.get("identity_key_type") or "").strip().lower()
    key_value = str(user.get("identity_key") or "").strip()
    if not issuer or key_type not in {"oid", "sub"} or not key_value:
        if selected_mode == "shadow":
            shadow = dict(user)
            shadow["identity_status"] = "shadow_invalid_identity"
            return shadow
        raise IdentityResolutionError("認証トークンに不変のEntra identity座標がありません")

    if repository is None:
        from shared.billing import repository as billing_repository

        repository = billing_repository

    if selected_mode == "shadow":
        try:
            binding = repository.find_active_identity_binding(
                token_issuer=issuer,
                subject_type=key_type,
                subject_value=key_value,
            )
        except Exception:
            logger.exception("Identity resolver shadow lookup failed")
            shadow = dict(user)
            shadow["identity_status"] = "shadow_lookup_error"
            return shadow
        if binding:
            return _observe_shadow_tenant(user, binding.get("tenant_id"), source="binding")
        try:
            legacy_candidate = repository.find_legacy_identity_candidate(
                entra_object_id=str(user.get("entra_object_id") or "").strip(),
            )
        except Exception:
            logger.exception("Identity resolver shadow legacy-candidate lookup failed")
            shadow = dict(user)
            shadow["identity_status"] = "shadow_candidate_lookup_error"
            return shadow
        if legacy_candidate:
            return _observe_shadow_tenant(
                user,
                legacy_candidate.get("tenant_id"),
                source="legacy",
            )
        shadow = dict(user)
        shadow["identity_status"] = "shadow_unbound"
        return shadow

    trust_binding_claims = identity_binding_claims_enabled()
    try:
        result = repository.resolve_or_provision_identity(
            token_issuer=issuer,
            directory_tenant_id=actual_directory_id,
            subject_type=key_type,
            subject_value=key_value,
            entra_object_id=str(user.get("entra_object_id") or "").strip(),
            token_subject=str(user.get("token_subject") or "").strip(),
            identity_provider=str(user.get("identity_provider") or "unknown").strip(),
            email=str(user.get("email") or "").strip(),
            display_name=str(user.get("name") or "").strip(),
            # ``extension_tenantId`` remains part of the legacy-mode response,
            # but it must not enter the canonical resolver until the Entra
            # custom-attribute write controls have been audited.  The verified
            # Entra object id is the only safe legacy bootstrap coordinate by
            # default.
            legacy_tenant_id=(
                str(user.get("legacy_tenant_id") or "").strip()
                if trust_binding_claims
                else str(user.get("entra_object_id") or "").strip()
            ),
            claimed_business_tenant_id=(
                str(user.get("claimed_business_tenant_id") or "").strip()
                if trust_binding_claims
                else ""
            ),
            claimed_principal_id=(
                str(user.get("claimed_principal_id") or "").strip()
                if trust_binding_claims
                else ""
            ),
            allow_auto_provision=(
                identity_auto_provision_enabled()
                if allow_auto_provision is None
                else bool(allow_auto_provision)
            ),
        )
    except IdentityResolutionError:
        raise
    except Exception as exc:
        logger.exception("Identity resolver enforce operation failed")
        raise IdentityResolverUnavailable("identity resolver is temporarily unavailable") from exc
    status = str(result.get("status") or "")
    if status == "link_required":
        raise IdentityLinkRequired("既存アカウントへの安全な連携が必要です")
    if status not in {
        "bound",
        "legacy_bootstrap",
        "provisioned",
        "entra_extension_binding",
        "entra_extension_bootstrap",
    }:
        raise IdentityResolutionError("このEntra identityはTECHIEアカウントに未連携です")
    return _apply_binding(user, result, status=status)
