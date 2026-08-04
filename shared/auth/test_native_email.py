from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException, Response

from shared.auth.nicegui_auth import _is_public

from shared.auth.native_email import (
    NativeEmailBroker,
    NativeEmailFlowError,
    NativeEmailSettings,
    _raise_http,
    _set_no_store,
)


def test_native_email_routes_are_public_before_a_token_exists():
    assert _is_public("/api/auth/native-email/status") is True
    assert _is_public("/api/auth/native-email/start") is True
    assert _is_public("/api/auth/native-email/verify") is True
    assert _is_public("/api/auth/native-email-extra/start") is False


def test_native_email_responses_are_never_cacheable():
    response = Response()
    _set_no_store(response)
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"

    with pytest.raises(HTTPException) as exc:
        _raise_http(NativeEmailFlowError("native_auth_unavailable", 503))
    assert exc.value.headers == {"Cache-Control": "no-store", "Pragma": "no-cache"}


def test_native_email_deployment_is_two_stage_and_fail_closed():
    root = Path(__file__).resolve().parents[2]
    deploy = (root / "deploy-azure0429-refresh.ps1").read_text(encoding="utf-8")
    wrapper = (root / "deploy-azure0429-refresh-kyotokyotechie.ps1").read_text(encoding="utf-8")
    template = (root / "techie-hub" / "config.template.js").read_text(encoding="utf-8")
    bicep = (root / "infra" / "main.bicep").read_text(encoding="utf-8")

    assert "[switch]$EnableNativeEmailBroker" in deploy
    assert "[switch]$PublishNativeEmail" in deploy
    assert "[switch]$ConfirmNativeEmailLiveVerified" in deploy
    assert "Publishing Native Email requires both" in deploy
    assert "EMAIL_NATIVE_AUTH_SESSION_KEY must decode to exactly 32 bytes" in deploy
    assert '"EMAIL_NATIVE_AUTH_ENABLED=$(if ($EnableNativeEmailBroker)' in deploy
    assert '"ENTRA_NATIVE_TENANT_SUBDOMAIN=$NativeAuthTenantSubdomain"' in deploy
    assert '"EMAIL_NATIVE_AUTH_SESSION_KEY=$nativeAuthSessionKey"' in deploy
    assert "$nativeEmailRuntimeSettings" in deploy
    assert "$optionalRuntimeSettings + $nativeEmailRuntimeSettings" in deploy
    assert "$commonWebSettings + $nativeEmailRuntimeSettings" in deploy
    assert "-NativeEmailEnabled ([bool]$PublishNativeEmail)" in deploy
    assert "-NativeEmailLiveVerified ([bool]$ConfirmNativeEmailLiveVerified)" in deploy
    assert "-EnableNativeEmailBroker:$EnableNativeEmailBroker" in wrapper
    assert "-PublishNativeEmail:$PublishNativeEmail" in wrapper
    assert "-ConfirmNativeEmailLiveVerified:$ConfirmNativeEmailLiveVerified" in wrapper
    assert "EMAIL_NATIVE_AUTH_ENABLED: %%EMAIL_NATIVE_AUTH_ENABLED%%" in template
    assert "EMAIL_NATIVE_AUTH_LIVE_VERIFIED: %%EMAIL_NATIVE_AUTH_LIVE_VERIFIED%%" in template
    assert "nativeEmailAuthLiveVerified" not in bicep
    assert "var effectiveNativeEmailAuth = nativeEmailAuthEnabled" in bicep


def test_hub_native_email_requests_reach_the_api_image_router():
    root = Path(__file__).resolve().parents[2]
    hub = (root / "techie-hub" / "index.html").read_text(encoding="utf-8")
    deploy = (root / "deploy-azure0429-refresh.ps1").read_text(encoding="utf-8")
    dockerfile = (root / "notecode" / "Dockerfile").read_text(encoding="utf-8")
    app_source = (root / "notecode" / "note" / "note_writer_app.py").read_text(encoding="utf-8")

    assert "fetch(`${config.API_BASE_URL}${endpoint}`" in hub
    assert "'/api/auth/native-email/start'" in hub
    assert "'/api/auth/native-email/verify'" in hub
    assert '-WebAppName $ApiWebAppName' in deploy
    assert '-ImageRef "$acrServer/kotomake:$tag"' in deploy
    assert 'CMD ["python", "-m", "note.note_writer_app"]' in dockerfile
    assert "from shared.auth.native_email import router as native_email_router" in app_source
    assert "app.include_router(native_email_router)" in app_source


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakePost:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        assert kwargs["allow_redirects"] is False
        assert kwargs["timeout"] == 8.0
        return self.responses.pop(0)


def settings(**overrides):
    values = {
        "enabled": True,
        "tenant_subdomain": "customer-directory",
        "client_id": "public-client-id",
        "session_key": b"k" * 32,
        "allowed_origins": frozenset({"https://app.example.test"}),
        "flow_ttl_seconds": 300,
        "request_timeout_seconds": 8.0,
        "rate_limit_attempts": 5,
        "rate_limit_window_seconds": 600,
    }
    values.update(overrides)
    return NativeEmailSettings(**values)


def sign_in_responses():
    return [
        FakeResponse(200, {"continuation_token": "init-token"}),
        FakeResponse(
            200,
            {
                "continuation_token": "challenge-token",
                "challenge_type": "oob",
                "challenge_channel": "email",
                "challenge_target_label": "u***@example.test",
                "code_length": 8,
            },
        ),
        FakeResponse(200, {"id_token": "signed-id-token", "access_token": "must-not-return", "expires_in": 3600}),
    ]


def test_settings_are_fail_closed_without_every_required_value():
    assert settings().ready is True
    assert settings(enabled=False).ready is False
    assert settings(tenant_subdomain="bad/path").ready is False
    assert settings(session_key=b"short").ready is False
    assert settings(allowed_origins=frozenset()).ready is False


def test_origin_must_be_explicitly_allowlisted():
    broker = NativeEmailBroker(settings(), post=FakePost([]), token_verifier=lambda _: {}, directory_id_getter=lambda: "external-directory")
    broker.require_origin("https://app.example.test/")
    with pytest.raises(NativeEmailFlowError) as exc:
        broker.require_origin("https://attacker.example")
    assert exc.value.code == "native_auth_origin_denied"


def test_sign_in_otp_flow_hides_continuation_and_returns_only_id_token():
    fake = FakePost(sign_in_responses())
    verified = []
    broker = NativeEmailBroker(
        settings(),
        post=fake,
        token_verifier=lambda token: verified.append(token) or {"sub": "subject", "tid": "external-directory"},
        directory_id_getter=lambda: "external-directory",
    )

    challenge = broker.start(
        email=" User@Example.Test ",
        intent="login",
        display_name="",
        client_key="client",
    )
    assert challenge["code_length"] == 8
    assert "continuation_token" not in challenge
    assert "challenge-token" not in challenge["flow_token"]
    assert fake.calls[0][0].endswith("/oauth2/v2.0/initiate")
    assert fake.calls[0][1]["data"]["username"] == "user@example.test"
    assert fake.calls[0][1]["data"]["challenge_type"] == "oob redirect"
    assert fake.calls[1][0].endswith("/oauth2/v2.0/challenge")

    result = broker.verify(flow_token=challenge["flow_token"], code="12345678")
    assert result == {"id_token": "signed-id-token", "expires_in": 3600, "intent": "login"}
    assert verified == ["signed-id-token"]
    token_request = fake.calls[2][1]["data"]
    assert token_request["grant_type"] == "oob"
    assert token_request["scope"] == "openid profile email"
    assert "offline_access" not in token_request["scope"]
    assert "access_token" not in result


def test_signup_sends_only_display_name_and_never_business_or_billing_keys():
    fake = FakePost(
        [
            FakeResponse(200, {"continuation_token": "signup-start"}),
            FakeResponse(
                200,
                {
                    "continuation_token": "signup-challenge",
                    "challenge_type": "oob",
                    "challenge_channel": "email",
                    "challenge_target_label": "n***@example.test",
                    "code_length": 6,
                },
            ),
            FakeResponse(200, {"continuation_token": "signup-complete"}),
            FakeResponse(200, {"id_token": "signup-id-token", "expires_in": 1200}),
        ]
    )
    broker = NativeEmailBroker(settings(), post=fake, token_verifier=lambda _: {"sub": "new-subject", "tid": "external-directory"}, directory_id_getter=lambda: "external-directory")
    challenge = broker.start(
        email="new@example.test",
        intent="signup",
        display_name=" New  User ",
        client_key="client",
    )
    attributes = json.loads(fake.calls[0][1]["data"]["attributes"])
    assert attributes == {"displayName": "New User"}
    serialized = json.dumps(fake.calls[0][1]["data"]).lower()
    for forbidden in ("tenant_id", "customer_account", "stripe", "extension_tenantid"):
        assert forbidden not in serialized

    result = broker.verify(flow_token=challenge["flow_token"], code="123456")
    assert result["intent"] == "signup"
    assert fake.calls[2][0].endswith("/signup/v1.0/continue")
    assert fake.calls[3][1]["data"]["grant_type"] == "continuation_token"
    assert fake.calls[3][1]["data"]["username"] == "new@example.test"


def test_redirect_challenge_requires_explicit_operator_fallback():
    fake = FakePost([FakeResponse(200, {"challenge_type": "redirect"})])
    broker = NativeEmailBroker(settings(), post=fake, token_verifier=lambda _: {}, directory_id_getter=lambda: "external-directory")
    with pytest.raises(NativeEmailFlowError) as exc:
        broker.start(email="user@example.test", intent="login", display_name="", client_key="client")
    assert exc.value.code == "native_auth_fallback_required"


def test_wrong_code_shape_never_reaches_token_endpoint():
    fake = FakePost(sign_in_responses()[:2])
    broker = NativeEmailBroker(settings(), post=fake, token_verifier=lambda _: {}, directory_id_getter=lambda: "external-directory")
    challenge = broker.start(email="user@example.test", intent="login", display_name="", client_key="client")
    with pytest.raises(NativeEmailFlowError) as exc:
        broker.verify(flow_token=challenge["flow_token"], code="1234")
    assert exc.value.code == "otp_invalid"
    assert len(fake.calls) == 2


def test_tampered_or_expired_flow_is_rejected_before_network():
    now = [1000.0]
    fake = FakePost(sign_in_responses()[:2])
    broker = NativeEmailBroker(settings(flow_ttl_seconds=1), post=fake, token_verifier=lambda _: {}, directory_id_getter=lambda: "external-directory", now=lambda: now[0])
    challenge = broker.start(email="user@example.test", intent="login", display_name="", client_key="client")
    now[0] = 1002.0
    with pytest.raises(NativeEmailFlowError) as expired:
        broker.verify(flow_token=challenge["flow_token"], code="12345678")
    assert expired.value.code == "native_flow_invalid"
    with pytest.raises(NativeEmailFlowError):
        broker.verify(flow_token=challenge["flow_token"][:-1] + "A", code="12345678")
    assert len(fake.calls) == 2


def test_rate_limit_is_keyed_without_retaining_email_address():
    fake = FakePost(sign_in_responses()[:2] * 2)
    broker = NativeEmailBroker(settings(rate_limit_attempts=1), post=fake, token_verifier=lambda _: {}, directory_id_getter=lambda: "external-directory")
    broker.start(email="user@example.test", intent="login", display_name="", client_key="client")
    with pytest.raises(NativeEmailFlowError) as exc:
        broker.start(email="user@example.test", intent="login", display_name="", client_key="client")
    assert exc.value.code == "native_auth_rate_limited"
    assert all("user@example.test" not in key for key in broker._limiter._events)


def test_signup_fails_closed_when_unexpected_required_attributes_remain():
    fake = FakePost(
        sign_in_responses()[:2]
        + [FakeResponse(400, {"error": "attributes_required", "required_attributes": [{"name": "custom"}]})]
    )
    broker = NativeEmailBroker(settings(), post=fake, token_verifier=lambda _: {}, directory_id_getter=lambda: "external-directory")
    challenge = broker.start(
        email="new@example.test",
        intent="signup",
        display_name="New User",
        client_key="client",
    )
    with pytest.raises(NativeEmailFlowError) as exc:
        broker.verify(flow_token=challenge["flow_token"], code="12345678")
    assert exc.value.code == "native_signup_attributes_not_supported"


def test_token_from_any_other_directory_is_rejected():
    fake = FakePost(sign_in_responses())
    broker = NativeEmailBroker(
        settings(),
        post=fake,
        token_verifier=lambda _: {"sub": "subject", "tid": "workforce-directory"},
        directory_id_getter=lambda: "external-directory",
    )
    challenge = broker.start(email="user@example.test", intent="login", display_name="", client_key="client")
    with pytest.raises(NativeEmailFlowError) as exc:
        broker.verify(flow_token=challenge["flow_token"], code="12345678")
    assert exc.value.code == "native_auth_token_rejected"
