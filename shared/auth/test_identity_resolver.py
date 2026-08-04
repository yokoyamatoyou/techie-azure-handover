from __future__ import annotations

import asyncio
import importlib.util
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import HTTPException

from shared.auth import api as identity_api
from shared.auth.identity_resolver import (
    IdentityLinkRequired,
    IdentityResolutionError,
    IdentityResolverUnavailable,
    RecentAuthenticationRequired,
    require_recent_authentication,
    resolve_user_info,
)
from shared.auth.jwt_validator import (
    configured_external_directory_id,
    extract_identity_context,
    extract_user_info,
    normalize_identity_provider,
)
from shared.billing import api as billing_api


def _load_billing_repository_without_postgres_connection():
    """Load repository logic for fake-cursor tests without opening a DB."""
    repository_path = Path(__file__).resolve().parents[1] / "billing" / "repository.py"
    spec = importlib.util.spec_from_file_location("techie_identity_repository_test_target", repository_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


billing_repository = _load_billing_repository_without_postgres_connection()


@pytest.fixture(autouse=True)
def configured_external_directory(monkeypatch):
    monkeypatch.delenv("ENTRA_EXTERNAL_ID_TENANT_ID", raising=False)
    monkeypatch.setenv("ENTRA_EXTERNAL_ID_DIRECTORY_ID", "external-directory")
    monkeypatch.delenv("AUTH_TRUST_ENTRA_BINDING_CLAIMS", raising=False)
    monkeypatch.setenv("IDENTITY_LINKING_ENABLED", "1")


def test_identity_linking_api_fails_closed_when_backend_flag_is_off(monkeypatch):
    monkeypatch.setenv("IDENTITY_LINKING_ENABLED", "0")
    user = {
        "identity_status": "bound",
        "principal_id": "principal",
        "identity_binding_id": "binding",
        "issued_at": str(int(time.time())),
    }
    with pytest.raises(HTTPException) as intent_error:
        asyncio.run(identity_api.create_link_intent(identity_api.LinkIntentRequest(provider="google"), user))
    assert intent_error.value.status_code == 503
    assert intent_error.value.detail["code"] == "identity_linking_unavailable"

    with pytest.raises(HTTPException) as complete_error:
        asyncio.run(identity_api.complete_link(identity_api.LinkCompleteRequest(state="x" * 32), user))
    assert complete_error.value.status_code == 503
    assert complete_error.value.detail["code"] == "identity_linking_unavailable"


class FakeIdentityRepository:
    def __init__(
        self,
        *,
        binding=None,
        legacy_candidate=None,
        result=None,
        fail_lookup=False,
        fail_resolve=False,
    ):
        self.binding = binding
        self.legacy_candidate = legacy_candidate
        self.result = result
        self.fail_lookup = fail_lookup
        self.fail_resolve = fail_resolve
        self.resolve_calls = []

    def find_active_identity_binding(self, **kwargs):
        if self.fail_lookup:
            raise RuntimeError("schema unavailable")
        return self.binding

    def resolve_or_provision_identity(self, **kwargs):
        if self.fail_resolve:
            raise RuntimeError("database unavailable")
        self.resolve_calls.append(kwargs)
        return dict(self.result or {"status": "unlinked"})

    def find_legacy_identity_candidate(self, **kwargs):
        return self.legacy_candidate


def verified_user(**overrides):
    user = {
        "user_id": "entra-object",
        "email": "person@example.test",
        "name": "Example Person",
        "tenant_id": "legacy-tenant",
        "legacy_tenant_id": "legacy-tenant",
        "claimed_business_tenant_id": "",
        "claimed_principal_id": "",
        "roles": "user",
        "identity_mode": "entra_external_id",
        "token_issuer": "https://issuer.example.test/v2.0",
        "directory_tenant_id": "external-directory",
        "identity_key_type": "oid",
        "identity_key": "entra-object",
        "entra_object_id": "entra-object",
        "token_subject": "token-subject",
        "identity_provider": "google",
        "issued_at": str(int(time.time())),
    }
    user.update(overrides)
    return user


def test_extract_identity_context_prefers_oid_and_normalizes_coordinates():
    context = extract_identity_context(
        {
            "iss": "HTTPS://Issuer.Example.test/v2.0/",
            "tid": "DIRECTORY-ID",
            "oid": "OBJECT-ID",
            "sub": "SUBJECT-ID",
            "emails": [" Person@Example.Test "],
            "idp": "google.com",
            "iat": 123,
        }
    )

    assert context == {
        "token_issuer": "https://issuer.example.test/v2.0",
        "directory_tenant_id": "directory-id",
        "identity_key_type": "oid",
        "identity_key": "OBJECT-ID",
        "entra_object_id": "OBJECT-ID",
        "token_subject": "SUBJECT-ID",
        "identity_provider": "google",
        "email": "Person@Example.Test",
        "issued_at": "123",
    }


def test_extract_user_info_keeps_legacy_coordinate_until_resolver_cutover():
    user = extract_user_info(
        {
            "iss": "https://issuer.example.test/v2.0",
            "tid": "external-directory",
            "oid": "00000000-0000-0000-0000-000000000001",
            "sub": "subject",
            "extension_tenantId": "00000000-0000-0000-0000-000000000002",
            "extension_principalId": "00000000-0000-0000-0000-000000000003",
        }
    )

    assert user["tenant_id"] == "00000000-0000-0000-0000-000000000002"
    assert user["legacy_tenant_id"] == user["tenant_id"]
    assert user["claimed_business_tenant_id"] == user["tenant_id"]
    assert user["claimed_principal_id"] == "00000000-0000-0000-0000-000000000003"
    assert user["identity_key_type"] == "oid"


def test_provider_evidence_is_normalized_to_login_choices():
    assert normalize_identity_provider("google.com") == "google"
    assert normalize_identity_provider("https://accounts.google.com/") == "google"
    assert normalize_identity_provider("live.com") == "microsoft"
    assert normalize_identity_provider(
        "https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/v2.0"
    ) == "microsoft"
    assert normalize_identity_provider("notgoogle.invalid") == "unknown"
    assert normalize_identity_provider("https://login.live.com.invalid/") == "unknown"
    assert normalize_identity_provider("") == "email"


def test_existing_tenant_id_setting_is_the_directory_guard(monkeypatch):
    monkeypatch.delenv("ENTRA_EXTERNAL_ID_DIRECTORY_ID", raising=False)
    monkeypatch.setenv("ENTRA_EXTERNAL_ID_TENANT_ID", "external-directory")
    assert configured_external_directory_id() == "external-directory"


def test_legacy_mode_does_not_access_repository_or_change_tenant():
    user = verified_user()
    result = resolve_user_info(user, mode="legacy", repository=object())

    assert result["tenant_id"] == "legacy-tenant"
    assert result["identity_status"] == "legacy"
    assert result["principal_id"] == ""


def test_shadow_mode_uses_binding_without_writing():
    repository = FakeIdentityRepository(
        binding={
            "tenant_id": "canonical-tenant",
            "principal_id": "canonical-principal",
            "identity_binding_id": "binding-id",
            "directory_tenant_id": "external-directory",
            "identity_provider": "google",
        }
    )

    result = resolve_user_info(verified_user(), mode="shadow", repository=repository)

    assert result["tenant_id"] == "legacy-tenant"
    assert result["principal_id"] == ""
    assert result["identity_status"] == "shadow_binding_tenant_mismatch"
    assert not any(key.startswith("shadow_") and key != "identity_status" for key in result)
    assert "shadow_principal_id" not in result
    assert repository.resolve_calls == []


def test_shadow_mode_records_a_match_without_exposing_canonical_coordinates():
    repository = FakeIdentityRepository(
        binding={
            "tenant_id": "legacy-tenant",
            "principal_id": "canonical-principal",
            "identity_binding_id": "binding-id",
            "directory_tenant_id": "external-directory",
            "identity_provider": "google",
        }
    )

    result = resolve_user_info(verified_user(), mode="shadow", repository=repository)

    assert result["identity_status"] == "shadow_binding_match"
    assert result["tenant_id"] == "legacy-tenant"
    assert result["principal_id"] == ""
    assert result["identity_binding_id"] == ""
    assert "shadow_principal_id" not in result
    assert "shadow_identity_binding_id" not in result


@pytest.mark.parametrize(
    ("binding_overrides", "expected_status"),
    [
        ({"directory_tenant_id": "workforce-directory"}, "shadow_binding_directory_mismatch"),
        ({"identity_provider": "microsoft"}, "shadow_binding_provider_mismatch"),
    ],
)
def test_shadow_binding_drift_fails_closed_without_exposing_coordinates(
    binding_overrides,
    expected_status,
):
    binding = {
        "tenant_id": "legacy-tenant",
        "principal_id": "canonical-principal",
        "identity_binding_id": "binding-id",
        "directory_tenant_id": "external-directory",
        "identity_provider": "google",
        **binding_overrides,
    }

    result = resolve_user_info(
        verified_user(),
        mode="shadow",
        repository=FakeIdentityRepository(binding=binding),
    )

    assert result["identity_status"] == expected_status
    assert result["tenant_id"] == "legacy-tenant"
    assert result["principal_id"] == ""
    assert result["identity_binding_id"] == ""


def test_shadow_mode_observes_verified_oid_legacy_candidate_without_writing():
    repository = FakeIdentityRepository(
        legacy_candidate={"tenant_id": "legacy-tenant"},
    )

    result = resolve_user_info(verified_user(), mode="shadow", repository=repository)

    assert result["identity_status"] == "shadow_legacy_match"
    assert result["tenant_id"] == "legacy-tenant"
    assert result["principal_id"] == ""
    assert repository.resolve_calls == []
    assert "shadow_tenant_id" not in result


def test_shadow_lookup_error_preserves_legacy_behavior():
    result = resolve_user_info(
        verified_user(),
        mode="shadow",
        repository=FakeIdentityRepository(fail_lookup=True),
    )

    assert result["tenant_id"] == "legacy-tenant"
    assert result["identity_status"] == "shadow_lookup_error"


@pytest.mark.parametrize(
    "status",
    [
        "bound",
        "legacy_bootstrap",
        "provisioned",
        "entra_extension_binding",
        "entra_extension_bootstrap",
    ],
)
def test_enforce_mode_applies_canonical_binding(status):
    repository = FakeIdentityRepository(
        result={
            "status": status,
            "tenant_id": "canonical-tenant",
            "principal_id": "canonical-principal",
            "identity_binding_id": "binding-id",
        }
    )

    result = resolve_user_info(
        verified_user(),
        mode="enforce",
        repository=repository,
        allow_auto_provision=True,
    )

    assert result["tenant_id"] == "canonical-tenant"
    assert result["user_id"] == "entra-object"
    assert result["principal_id"] == "canonical-principal"
    assert result["identity_status"] == status
    assert repository.resolve_calls[0]["email"] == "person@example.test"


def test_enforce_mode_ignores_entra_management_claims_by_default():
    repository = FakeIdentityRepository(
        result={
            "status": "entra_extension_binding",
            "tenant_id": "canonical-tenant",
            "principal_id": "canonical-principal",
            "identity_binding_id": "binding-id",
        }
    )
    resolve_user_info(
        verified_user(
            claimed_business_tenant_id="00000000-0000-0000-0000-000000000020",
            claimed_principal_id="00000000-0000-0000-0000-000000000021",
        ),
        mode="enforce",
        repository=repository,
    )

    call = repository.resolve_calls[0]
    assert call["legacy_tenant_id"] == "entra-object"
    assert call["claimed_business_tenant_id"] == ""
    assert call["claimed_principal_id"] == ""


def test_enforce_mode_forwards_entra_management_claims_only_after_opt_in(monkeypatch):
    monkeypatch.setenv("AUTH_TRUST_ENTRA_BINDING_CLAIMS", "1")
    repository = FakeIdentityRepository(
        result={
            "status": "entra_extension_binding",
            "tenant_id": "canonical-tenant",
            "principal_id": "canonical-principal",
            "identity_binding_id": "binding-id",
        }
    )
    resolve_user_info(
        verified_user(
            claimed_business_tenant_id="00000000-0000-0000-0000-000000000020",
            claimed_principal_id="00000000-0000-0000-0000-000000000021",
        ),
        mode="enforce",
        repository=repository,
    )

    call = repository.resolve_calls[0]
    assert call["claimed_business_tenant_id"] == "00000000-0000-0000-0000-000000000020"
    assert call["claimed_principal_id"] == "00000000-0000-0000-0000-000000000021"


def test_enforce_mode_never_auto_links_an_email_collision():
    repository = FakeIdentityRepository(result={"status": "link_required"})

    with pytest.raises(IdentityLinkRequired):
        resolve_user_info(
            verified_user(),
            mode="enforce",
            repository=repository,
            allow_auto_provision=True,
        )


def test_enforce_mode_fails_closed_when_unlinked_and_auto_provision_is_off():
    with pytest.raises(IdentityResolutionError):
        resolve_user_info(
            verified_user(),
            mode="enforce",
            repository=FakeIdentityRepository(result={"status": "unlinked"}),
            allow_auto_provision=False,
        )


def test_enforce_mode_rejects_the_workforce_directory():
    with pytest.raises(IdentityResolutionError):
        resolve_user_info(
            verified_user(directory_tenant_id="workforce-directory"),
            mode="enforce",
            repository=FakeIdentityRepository(result={"status": "bound"}),
        )


def test_enforce_mode_fails_closed_when_identity_store_is_unavailable():
    with pytest.raises(IdentityResolverUnavailable):
        resolve_user_info(
            verified_user(),
            mode="enforce",
            repository=FakeIdentityRepository(fail_resolve=True),
        )


def test_recent_authentication_rejects_missing_or_stale_iat():
    with pytest.raises(RecentAuthenticationRequired):
        require_recent_authentication(verified_user(issued_at=""))
    with pytest.raises(RecentAuthenticationRequired):
        require_recent_authentication(verified_user(issued_at=str(int(time.time()) - 601)))


def test_recent_authentication_accepts_fresh_iat():
    require_recent_authentication(verified_user(issued_at=str(int(time.time()) - 30)))


@pytest.mark.parametrize("provider", ["email", "google", "microsoft"])
def test_bound_provider_checkout_reuses_canonical_tenant_and_customer_anchor(monkeypatch, provider):
    canonical_tenant = "00000000-0000-0000-0000-000000000301"
    existing_customer_anchor = "synthetic-existing-customer"
    captured = {}

    def fake_ensure_customer_account(**kwargs):
        captured["account"] = kwargs
        return {"stripe_customer_id": existing_customer_anchor}

    def customer_creation_must_not_run(**kwargs):
        raise AssertionError("an existing customer anchor must not be replaced")

    def fake_create_checkout_session(**kwargs):
        captured["checkout"] = kwargs
        return {"session_id": "synthetic-session", "url": "https://checkout.example.invalid/session"}

    monkeypatch.setattr(billing_api.repository, "ensure_customer_account", fake_ensure_customer_account)
    monkeypatch.setattr(billing_api, "create_customer", customer_creation_must_not_run)
    monkeypatch.setattr(billing_api, "create_checkout_session", fake_create_checkout_session)
    monkeypatch.setattr(billing_api, "_allowed_stripe_price_ids", lambda: {"synthetic-price"})

    payload = billing_api.CheckoutSessionRequest(
        price_id="synthetic-price",
        success_url="https://app.techie.jp/checkout/success",
        cancel_url="https://app.techie.jp/plans",
        service_code="synthetic-service",
        service_name="Synthetic service",
        company_name="Synthetic company",
    )
    result = asyncio.run(
        billing_api.billing_checkout_session(
            payload,
            {
                "tenant_id": canonical_tenant,
                "user_id": "00000000-0000-0000-0000-000000000302",
                "email": "synthetic@example.invalid",
                "name": "Synthetic user",
                "identity_provider": provider,
            },
        )
    )

    assert result["session_id"] == "synthetic-session"
    assert captured["account"]["tenant_id"] == canonical_tenant
    assert captured["checkout"]["customer_id"] == existing_customer_anchor
    assert captured["checkout"]["metadata"]["tenant_id"] == canonical_tenant


def test_link_intent_requires_a_canonical_binding():
    user = verified_user(identity_status="legacy", principal_id="", identity_binding_id="")

    with pytest.raises(HTTPException) as error:
        asyncio.run(identity_api.create_link_intent(identity_api.LinkIntentRequest(provider="google"), user))

    assert error.value.status_code == 409


def test_link_intent_stores_only_a_digest(monkeypatch):
    captured = {}

    def fake_create_identity_link_intent(**kwargs):
        captured.update(kwargs)
        return {"identity_link_intent_id": "intent", "expires_at": "later"}

    fake_repository = type(
        "FakeLinkRepository",
        (),
        {"create_identity_link_intent": staticmethod(fake_create_identity_link_intent)},
    )()
    monkeypatch.setattr(identity_api, "_repository", lambda: fake_repository)
    user = verified_user(
        identity_status="bound",
        principal_id="00000000-0000-0000-0000-000000000010",
        identity_binding_id="00000000-0000-0000-0000-000000000011",
    )

    response = asyncio.run(
        identity_api.create_link_intent(identity_api.LinkIntentRequest(provider="google"), user)
    )

    assert response["provider"] == "google"
    assert response["state"] not in captured.values()
    assert len(captured["state_digest"]) == 64


def test_link_intent_rejects_microsoft_sso_before_repository(monkeypatch):
    class RepositoryMustNotRun:
        @staticmethod
        def create_identity_link_intent(**kwargs):
            raise AssertionError("repository must not run for disabled Microsoft SSO")

    monkeypatch.setattr(identity_api, "_repository", lambda: RepositoryMustNotRun())

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            identity_api.create_link_intent(
                identity_api.LinkIntentRequest(provider="microsoft"),
                verified_user(),
            )
        )

    assert error.value.status_code == 400
    assert error.value.detail == "provider must be email or google"


def test_repository_rejects_microsoft_link_intent_before_database(monkeypatch):
    @contextmanager
    def database_must_not_run(*args, **kwargs):
        raise AssertionError("database must not run for disabled Microsoft SSO")
        yield

    monkeypatch.setattr(billing_repository, "get_cursor", database_must_not_run)

    with pytest.raises(ValueError, match="not enabled for account linking"):
        billing_repository.create_identity_link_intent(
            principal_id="00000000-0000-0000-0000-000000000010",
            source_identity_binding_id="00000000-0000-0000-0000-000000000011",
            state_digest="a" * 64,
            requested_provider="microsoft",
        )


def test_link_complete_fails_closed_on_cross_principal_conflict(monkeypatch):
    fake_repository = type(
        "FakeLinkRepository",
        (),
        {"complete_identity_link": staticmethod(lambda **kwargs: {"status": "conflict"})},
    )()
    monkeypatch.setattr(identity_api, "_repository", lambda: fake_repository)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            identity_api.complete_link(
                identity_api.LinkCompleteRequest(state="x" * 43),
                verified_user(),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail["code"] == "identity_already_linked"


def test_link_complete_rejects_non_external_directory_before_repository(monkeypatch):
    class RepositoryMustNotRun:
        @staticmethod
        def complete_identity_link(**kwargs):
            raise AssertionError("repository must not run for a workforce token")

    monkeypatch.setattr(identity_api, "_repository", lambda: RepositoryMustNotRun())

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            identity_api.complete_link(
                identity_api.LinkCompleteRequest(state="x" * 43),
                verified_user(directory_tenant_id="workforce-directory"),
            )
        )

    assert error.value.status_code == 403
    assert error.value.detail["code"] == "external_directory_mismatch"


def test_link_completion_requires_an_explicit_external_directory_setting(monkeypatch):
    monkeypatch.delenv("ENTRA_EXTERNAL_ID_DIRECTORY_ID", raising=False)
    monkeypatch.delenv("ENTRA_EXTERNAL_ID_TENANT_ID", raising=False)

    with pytest.raises(HTTPException) as error:
        identity_api._require_external_directory(verified_user())

    assert error.value.status_code == 503
    assert error.value.detail["code"] == "external_directory_not_configured"


def test_link_complete_fails_closed_on_provider_mismatch(monkeypatch):
    fake_repository = type(
        "FakeLinkRepository",
        (),
        {"complete_identity_link": staticmethod(lambda **kwargs: {"status": "provider_mismatch"})},
    )()
    monkeypatch.setattr(identity_api, "_repository", lambda: fake_repository)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            identity_api.complete_link(
                identity_api.LinkCompleteRequest(state="x" * 43),
                verified_user(),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail["code"] == "identity_provider_mismatch"


def test_link_complete_fails_closed_on_stored_directory_mismatch(monkeypatch):
    fake_repository = type(
        "FakeLinkRepository",
        (),
        {"complete_identity_link": staticmethod(lambda **kwargs: {"status": "directory_mismatch"})},
    )()
    monkeypatch.setattr(identity_api, "_repository", lambda: fake_repository)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            identity_api.complete_link(
                identity_api.LinkCompleteRequest(state="x" * 43),
                verified_user(),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail["code"] == "identity_directory_mismatch"


@pytest.mark.parametrize(
    ("repository_status", "expected_code"),
    [
        ("same_identity", "identity_same_as_source"),
        ("already_used", "identity_link_state_already_used"),
    ],
)
def test_link_complete_fails_closed_on_same_identity_or_used_state(
    monkeypatch,
    repository_status,
    expected_code,
):
    fake_repository = type(
        "FakeLinkRepository",
        (),
        {"complete_identity_link": staticmethod(lambda **kwargs: {"status": repository_status})},
    )()
    monkeypatch.setattr(identity_api, "_repository", lambda: fake_repository)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            identity_api.complete_link(
                identity_api.LinkCompleteRequest(state="x" * 43),
                verified_user(),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail["code"] == expected_code


class FakeLinkCompletionCursor:
    def __init__(self, *, intent_status, completed_match=False, existing=None, requested_provider="google"):
        self.intent_status = intent_status
        self.completed_match = completed_match
        self.existing = existing
        self.requested_provider = requested_provider
        self.row = None
        self.statements = []

    def execute(self, query, params=()):
        statement = " ".join(str(query).split())
        self.statements.append(statement)
        self.row = None
        if "pg_advisory_xact_lock" in statement:
            return
        if "FROM identity_link_intent ili" in statement:
            self.row = {
                "identity_link_intent_id": "00000000-0000-0000-0000-000000000100",
                "principal_id": "00000000-0000-0000-0000-000000000101",
                "source_identity_binding_id": "00000000-0000-0000-0000-000000000102",
                "requested_provider": self.requested_provider,
                "status": self.intent_status,
                "expires_at": "later",
                "completed_identity_binding_id": "00000000-0000-0000-0000-000000000103",
                "tenant_id": "00000000-0000-0000-0000-000000000104",
            }
            return
        if statement.startswith("SELECT now() >="):
            self.row = {"expired": False}
            return
        if "FROM external_identity_binding eib" in statement:
            self.row = self.existing
            return
        if "WHERE identity_binding_id = %s::uuid" in statement:
            self.row = {"matched": 1} if self.completed_match else None
            return
        if statement.startswith("INSERT INTO external_identity_binding"):
            self.row = {"identity_binding_id": "00000000-0000-0000-0000-000000000105"}
            return
        if statement.startswith("UPDATE identity_link_intent") or statement.startswith(
            "INSERT INTO identity_link_audit_log"
        ):
            return
        raise AssertionError(f"unexpected SQL in fake cursor: {statement}")

    def fetchone(self):
        return self.row


def _complete_with_fake_cursor(monkeypatch, cursor, *, identity_provider="google"):
    @contextmanager
    def fake_get_cursor(*args, **kwargs):
        yield cursor

    monkeypatch.setattr(billing_repository, "get_cursor", fake_get_cursor)
    return billing_repository.complete_identity_link(
        state_digest="a" * 64,
        token_issuer="https://issuer.example.test/v2.0",
        directory_tenant_id="external-directory",
        subject_type="oid",
        subject_value="second-object",
        entra_object_id="second-object",
        token_subject="second-subject",
        identity_provider=identity_provider,
        email="second@example.test",
    )


def test_completed_link_state_is_idempotent_only_for_the_same_second_identity(monkeypatch):
    matching = FakeLinkCompletionCursor(intent_status="completed", completed_match=True)
    assert _complete_with_fake_cursor(monkeypatch, matching)["status"] == "completed"

    different = FakeLinkCompletionCursor(intent_status="completed", completed_match=False)
    assert _complete_with_fake_cursor(monkeypatch, different)["status"] == "already_used"


def test_linking_the_source_identity_to_itself_is_cancelled(monkeypatch):
    source_binding = {
        "identity_binding_id": "00000000-0000-0000-0000-000000000102",
        "principal_id": "00000000-0000-0000-0000-000000000101",
        "tenant_id": "00000000-0000-0000-0000-000000000104",
        "directory_tenant_id": "external-directory",
        "identity_provider": "google",
        "link_method": "legacy_bootstrap",
        "status": "active",
    }
    cursor = FakeLinkCompletionCursor(intent_status="pending", existing=source_binding)

    assert _complete_with_fake_cursor(monkeypatch, cursor)["status"] == "same_identity"
    assert any("'same_identity'" in statement for statement in cursor.statements)
    assert any("FOR UPDATE OF ili, source_eib, cp" in statement for statement in cursor.statements)
    assert any("FOR UPDATE OF eib, cp" in statement for statement in cursor.statements)


def test_linking_an_existing_binding_with_stored_directory_drift_is_cancelled(monkeypatch):
    drifted_binding = {
        "identity_binding_id": "00000000-0000-0000-0000-000000000106",
        "principal_id": "00000000-0000-0000-0000-000000000101",
        "tenant_id": "00000000-0000-0000-0000-000000000104",
        "directory_tenant_id": "workforce-directory",
        "identity_provider": "google",
        "link_method": "reauthenticated_link",
        "status": "active",
    }
    cursor = FakeLinkCompletionCursor(intent_status="pending", existing=drifted_binding)

    assert _complete_with_fake_cursor(monkeypatch, cursor) == {"status": "directory_mismatch"}
    assert any("'directory_mismatch'" in statement for statement in cursor.statements)
    assert not any("INSERT INTO external_identity_binding" in statement for statement in cursor.statements)
    assert not any("customer_account" in statement for statement in cursor.statements)
    assert not any("stripe" in statement.lower() for statement in cursor.statements)


def test_reauthenticated_link_changes_only_identity_tables_and_keeps_business_tenant(monkeypatch):
    cursor = FakeLinkCompletionCursor(intent_status="pending", existing=None)

    result = _complete_with_fake_cursor(monkeypatch, cursor)

    assert result == {
        "status": "completed",
        "principal_id": "00000000-0000-0000-0000-000000000101",
        "tenant_id": "00000000-0000-0000-0000-000000000104",
        "identity_binding_id": "00000000-0000-0000-0000-000000000105",
    }
    mutation_sql = [
        statement
        for statement in cursor.statements
        if statement.startswith("INSERT ") or statement.startswith("UPDATE ")
    ]
    assert any("INSERT INTO external_identity_binding" in statement for statement in mutation_sql)
    assert any("UPDATE identity_link_intent" in statement for statement in mutation_sql)
    assert any("INSERT INTO identity_link_audit_log" in statement for statement in mutation_sql)
    assert not any("customer_account" in statement for statement in mutation_sql)
    assert not any("stripe" in statement.lower() for statement in mutation_sql)
    assert not any("UPDATE tenants" in statement for statement in mutation_sql)
    assert not any("UPDATE canonical_principal" in statement for statement in mutation_sql)


def test_pending_microsoft_link_intent_is_cancelled_without_binding_mutation(monkeypatch):
    cursor = FakeLinkCompletionCursor(intent_status="pending", requested_provider="microsoft")

    result = _complete_with_fake_cursor(monkeypatch, cursor, identity_provider="microsoft")

    assert result == {"status": "provider_mismatch"}
    assert any("'provider_mismatch'" in statement for statement in cursor.statements)
    assert not any("INSERT INTO external_identity_binding" in statement for statement in cursor.statements)
    assert not any("customer_account" in statement for statement in cursor.statements)
    assert not any("stripe" in statement.lower() for statement in cursor.statements)


class ExistingBindingCursor:
    def __init__(self, binding):
        self.binding = dict(binding)
        self.row = None
        self.statements = []

    def execute(self, query, params=()):
        statement = " ".join(str(query).split())
        self.statements.append(statement)
        self.row = None
        if "pg_advisory_xact_lock" in statement:
            return
        if "FROM external_identity_binding eib" in statement:
            self.row = dict(self.binding)
            return
        raise AssertionError(f"binding drift reached unexpected SQL: {statement}")

    def fetchone(self):
        return self.row


def _resolve_existing_binding_with_cursor(monkeypatch, cursor, *, provider="google"):
    @contextmanager
    def fake_get_cursor(*args, **kwargs):
        yield cursor

    monkeypatch.setattr(billing_repository, "get_cursor", fake_get_cursor)
    return billing_repository.resolve_or_provision_identity(
        token_issuer="https://issuer.example.test/v2.0",
        directory_tenant_id="external-directory",
        subject_type="oid",
        subject_value="existing-object",
        entra_object_id="existing-object",
        token_subject="existing-subject",
        identity_provider=provider,
        email="person@example.test",
        display_name="Example",
        legacy_tenant_id="",
        claimed_business_tenant_id="",
        claimed_principal_id="",
        allow_auto_provision=False,
    )


@pytest.mark.parametrize("provider", ["email", "google", "microsoft"])
def test_repository_existing_binding_accepts_each_provider_without_tenant_or_billing_mutation(
    monkeypatch,
    provider,
):
    cursor = ExistingBindingCursor(
        {
            "identity_binding_id": "00000000-0000-0000-0000-000000000201",
            "principal_id": "00000000-0000-0000-0000-000000000202",
            "tenant_id": "00000000-0000-0000-0000-000000000203",
            "directory_tenant_id": "external-directory",
            "identity_provider": provider,
            "link_method": "reauthenticated_link",
            "status": "active",
        }
    )

    result = _resolve_existing_binding_with_cursor(monkeypatch, cursor, provider=provider)

    assert result["status"] == "bound"
    assert result["tenant_id"] == "00000000-0000-0000-0000-000000000203"
    assert not any(statement.startswith("INSERT ") or statement.startswith("UPDATE ") for statement in cursor.statements)
    assert not any("customer_account" in statement or "stripe" in statement.lower() for statement in cursor.statements)


@pytest.mark.parametrize(
    ("binding_overrides", "provider", "expected_status"),
    [
        ({"directory_tenant_id": "workforce-directory"}, "google", "directory_mismatch"),
        ({"identity_provider": "microsoft"}, "google", "provider_mismatch"),
    ],
)
def test_repository_existing_binding_rejects_directory_or_provider_drift_before_mutation(
    monkeypatch,
    binding_overrides,
    provider,
    expected_status,
):
    binding = {
        "identity_binding_id": "00000000-0000-0000-0000-000000000201",
        "principal_id": "00000000-0000-0000-0000-000000000202",
        "tenant_id": "00000000-0000-0000-0000-000000000203",
        "directory_tenant_id": "external-directory",
        "identity_provider": "google",
        "link_method": "reauthenticated_link",
        "status": "active",
        **binding_overrides,
    }
    cursor = ExistingBindingCursor(binding)

    result = _resolve_existing_binding_with_cursor(monkeypatch, cursor, provider=provider)

    assert result == {"status": expected_status}
    assert not any(statement.startswith("INSERT ") or statement.startswith("UPDATE ") for statement in cursor.statements)


def test_unknown_provider_cannot_create_a_new_binding(monkeypatch):
    class UnknownProviderCursor:
        def __init__(self):
            self.row = None
            self.statements = []

        def execute(self, query, params=()):
            statement = " ".join(str(query).split())
            self.statements.append(statement)
            if "pg_advisory_xact_lock" not in statement and "FROM external_identity_binding eib" not in statement:
                raise AssertionError(f"unknown provider reached mutation SQL: {statement}")
            self.row = None

        def fetchone(self):
            return self.row

    cursor = UnknownProviderCursor()

    @contextmanager
    def fake_get_cursor(*args, **kwargs):
        yield cursor

    monkeypatch.setattr(billing_repository, "get_cursor", fake_get_cursor)
    result = billing_repository.resolve_or_provision_identity(
        token_issuer="https://issuer.example.test/v2.0",
        directory_tenant_id="external-directory",
        subject_type="oid",
        subject_value="unknown-provider-object",
        entra_object_id="unknown-provider-object",
        token_subject="unknown-provider-subject",
        identity_provider="notgoogle.invalid",
        email="person@example.test",
        display_name="Example",
        legacy_tenant_id="",
        claimed_business_tenant_id="",
        claimed_principal_id="",
        allow_auto_provision=True,
    )

    assert result == {"status": "unknown_provider"}
    assert not any(statement.startswith("INSERT ") for statement in cursor.statements)


def test_identity_schema_migration_is_additive_and_collision_guarded():
    root = Path(__file__).resolve().parents[2]
    migration = (root / "infra" / "20260803_identity_binding.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS public.canonical_principal" in migration
    assert "CREATE TABLE IF NOT EXISTS public.external_identity_binding" in migration
    assert "CREATE TABLE IF NOT EXISTS public.identity_link_intent" in migration
    assert "CREATE UNIQUE INDEX IF NOT EXISTS ux_external_identity_binding_coordinate" in migration
    assert "chk_identity_link_intent_provider" in migration
    assert "email_fingerprint" in migration
    assert "email_normalized" not in migration
    assert "public.techie_identity_set_row_updated_at" in migration
    assert "EXECUTE FUNCTION set_row_updated_at()" not in migration
    assert "UPDATE tenants" not in migration
    assert "UPDATE customer_account" not in migration
    assert "DELETE FROM" not in migration
    assert "DROP TABLE" not in migration


def test_repository_fails_closed_on_email_races_and_unknown_provider_evidence():
    root = Path(__file__).resolve().parents[2]
    repository = (root / "shared" / "billing" / "repository.py").read_text(encoding="utf-8")

    assert 'identity-email|{email_fingerprint}' in repository
    assert 'email_fingerprint=_identity_email_fingerprint(email)' in repository
    assert "observed_provider = requested_provider" not in repository
    assert "email_normalized" not in repository


def test_identity_migration_runner_is_hash_pinned_and_dry_run_by_default():
    root = Path(__file__).resolve().parents[2]
    runner = (root / "infra" / "20260803_identity_binding_runner.js").read_text(encoding="utf-8")

    assert "29D71CBE7F53739858BD499D009CF9527782F3E67D21F745D8FB73DAF074DBCB" in runner
    assert "argv.includes('--apply')" in runner
    assert "APPLY_HASH_CONFIRMATION_REQUIRED" in runner
    assert "await client.query('ROLLBACK')" in runner
    assert "SET LOCAL search_path = public, pg_catalog" in runner
    assert "SET LOCAL lock_timeout = '5s'" in runner
    assert "SET LOCAL statement_timeout = '60s'" in runner
    assert "commit_state=" in runner
    assert "DATABASE_URL is read from the process environment and is never printed" in runner
    assert "if (require.main === module)" in runner


def test_hub_exposes_email_and_google_only_and_keeps_microsoft_sso_disabled():
    root = Path(__file__).resolve().parents[2]
    hub = (root / "techie-hub" / "index.html").read_text(encoding="utf-8")

    assert 'data-auth-provider="email"' in hub
    assert 'data-auth-provider="google"' in hub
    assert 'Microsoftで${action}' not in hub
    assert 'data-auth-provider="microsoft"' not in hub
    assert '/auth-provider-policy.js?v=20260804b' in hub
    assert "microsoft: 'login.live.com'" not in hub
    assert "providerEnabled(provider)" in hub
    assert "同じ契約・請求管理へ戻ります" in hub
    assert "Stripeの顧客情報をログイン方法として表示したり" in hub
    assert 'data-link-provider="microsoft"' not in hub
    assert "renderLogin('signup')" in hub
    assert "startLogin('signup');" not in hub
    assert "Microsoft系のメールアドレスも利用できます" in hub
    assert "Outlook、Hotmail、Microsoft 365の会社メール" in hub

    config_template = (root / "techie-hub" / "config.template.js").read_text(encoding="utf-8")
    assert "MICROSOFT_AUTH_" not in config_template

    provider_policy = (root / "techie-hub" / "auth-provider-policy.js").read_text(encoding="utf-8")
    hub_dockerfile = (root / "techie-hub" / "Dockerfile").read_text(encoding="utf-8")
    assert "if (provider === 'microsoft') return false;" in provider_policy
    assert "config.GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED === true" in provider_policy
    assert "authRequest(provider, intent, config)" in hub
    assert "COPY auth-provider-policy.js /usr/share/nginx/html/auth-provider-policy.js" in hub_dockerfile
    assert "/api/identity/link-intents" in hub
    assert "/api/identity/link-complete" in hub
    assert "purpose === 'link_source'" in hub
    assert "purpose === 'link_target'" in hub
    assert "apiFetchWithToken('/api/identity/link-complete'" in hub
    assert "clearStoredAuthToken(true)" in hub
    assert "clearStoredAuthToken(true);\n      syncAccount();" in hub
    assert "IDENTITY_LINK_SOURCE_TOKEN" not in hub
    start_login = hub[hub.index("async function startLogin(") : hub.index("async function openCheckout(")]
    assert start_login.index("if (provider === 'email' && nativeEmailEnabled())") < start_login.index("if (!msalClient)")


def test_nicegui_saved_tenant_cannot_bypass_nonlegacy_resolver():
    root = Path(__file__).resolve().parents[2]
    helper = (root / "shared" / "auth" / "nicegui_identity.py").read_text(encoding="utf-8")

    assert 'identity_resolver_mode() == "legacy"' in helper
    assert '_ROUTE_VERIFIED_IDENTITY_PATHS = frozenset({"/api/identity/link-complete"})' in (
        root / "shared" / "auth" / "nicegui_auth.py"
    ).read_text(encoding="utf-8")


def test_deployment_entrypoints_fail_safe_until_identity_schema_is_verified():
    root = Path(__file__).resolve().parents[2]

    for script_name in ("deploy-azure0429-refresh.ps1", "deploy-kotomegane.ps1"):
        script = (root / script_name).read_text(encoding="utf-8")

        assert "[ValidateSet('legacy','shadow','enforce')]" in script
        assert "$IdentityResolverMode = 'legacy'" in script
        assert "[switch]$IdentitySchemaVerified" in script
        assert "$IdentityResolverMode -ne 'legacy' -and -not $IdentitySchemaVerified" in script
        assert "$IdentityResolverMode -ne 'legacy' -and [string]::IsNullOrWhiteSpace($ExternalTenantId)" in script
        assert "AUTH_IDENTITY_RESOLVER_MODE=$IdentityResolverMode" in script
        assert "AUTH_IDENTITY_AUTO_PROVISION=" in script
        assert "AUTH_TRUST_ENTRA_BINDING_CLAIMS=" in script

    bicep = (root / "infra" / "main.bicep").read_text(encoding="utf-8")

    assert "param identityResolverMode string = 'legacy'" in bicep
    assert "param identitySchemaVerified bool = false" in bicep
    assert "identitySchemaVerified && !empty(b2cTenantId) ? identityResolverMode : 'legacy'" in bicep
    assert "effectiveIdentityResolverMode == 'enforce' && identityAutoProvision" in bicep
    assert "effectiveIdentityResolverMode == 'enforce' && trustEntraBindingClaims" in bicep
    assert bicep.count("{ name: 'AUTH_IDENTITY_RESOLVER_MODE'") == 3
    assert bicep.count("{ name: 'AUTH_IDENTITY_AUTO_PROVISION'") == 3
    assert bicep.count("{ name: 'AUTH_TRUST_ENTRA_BINDING_CLAIMS'") == 3
    assert bicep.count("{ name: 'ENTRA_EXTERNAL_ID_TENANT_ID'") == 3
