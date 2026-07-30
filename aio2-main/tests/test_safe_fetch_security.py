from __future__ import annotations

from typing import Any

import pytest

import core.safe_fetch as safe_fetch_mod
from core.safe_fetch import ResolvedTarget, UnsafeURLError, safe_fetch_url, validate_public_url


class _FakeResponse:
    def __init__(self, status_code: int = 200, *, headers: dict[str, str] | None = None, body: bytes = b"ok") -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self._body = body
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.closed = False

    def iter_content(self, chunk_size: int = 65536):  # type: ignore[no-untyped-def]
        yield self._body

    def close(self) -> None:
        self.closed = True


class _FakeSession:
    def close(self) -> None:
        return None


def _make_addrinfo(ip: str) -> list[tuple[Any, ...]]:
    return _make_addrinfos(ip)


def _make_addrinfos(*ips: str) -> list[tuple[Any, ...]]:
    return [
        (2 if ":" not in ip else 10, 1, 6, "", (ip, 0))
        for ip in ips
    ]


def test_validate_public_url_allows_global_nat64_with_public_ipv4(monkeypatch) -> None:
    monkeypatch.setattr(
        safe_fetch_mod.socket,
        "getaddrinfo",
        lambda host, port: _make_addrinfos("64:ff9b::997d:8de4", "153.125.141.228"),
    )

    target = validate_public_url("https://www.d-w-c.jp/")

    assert target.resolved_ips == ("64:ff9b::997d:8de4", "153.125.141.228")
    assert target.connect_ip == "153.125.141.228"


def test_validate_public_url_rejects_non_global_shared_address(monkeypatch) -> None:
    monkeypatch.setattr(safe_fetch_mod.socket, "getaddrinfo", lambda host, port: _make_addrinfo("100.64.0.1"))

    with pytest.raises(UnsafeURLError) as exc_info:
        validate_public_url("https://example.com/")

    assert exc_info.value.reason == "private_ip_not_allowed"


def test_safe_fetch_uses_validated_ip_even_if_dns_rebinds(monkeypatch) -> None:
    state = {"calls": 0}

    def fake_getaddrinfo(host: str, port: int | None):  # type: ignore[no-untyped-def]
        if host != "example.com":
            return _make_addrinfo("203.0.113.10")
        state["calls"] += 1
        if state["calls"] == 1:
            return _make_addrinfo("93.184.216.34")
        return _make_addrinfo("127.0.0.1")

    captured: list[str] = []

    def fake_send(target: ResolvedTarget, *, headers: dict, timeout: float):  # type: ignore[no-untyped-def]
        rebound_ip = fake_getaddrinfo(target.hostname, None)[0][4][0]
        assert rebound_ip == "127.0.0.1"
        captured.append(target.connect_ip)
        return _FakeSession(), _FakeResponse(200, body=b"public")

    monkeypatch.setattr(safe_fetch_mod.socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(safe_fetch_mod, "_send_fixed_ip_request", fake_send)

    response = safe_fetch_url("https://example.com/path")

    assert captured == ["93.184.216.34"]
    assert response.safe_final_ip == "93.184.216.34"
    assert response.safe_redirect_chain == ["https://example.com/path"]
    assert response._content == b"public"


def test_safe_fetch_validates_each_redirect_hop(monkeypatch) -> None:
    ip_map = {
        "first.example": "93.184.216.34",
        "second.example": "93.184.216.35",
    }

    def fake_getaddrinfo(host: str, port: int | None):  # type: ignore[no-untyped-def]
        return _make_addrinfo(ip_map[host])

    seen: list[tuple[str, str]] = []

    def fake_send(target: ResolvedTarget, *, headers: dict, timeout: float):  # type: ignore[no-untyped-def]
        seen.append((target.hostname, target.connect_ip))
        if target.hostname == "first.example":
            return _FakeSession(), _FakeResponse(
                302,
                headers={"Location": "https://second.example/final"},
            )
        return _FakeSession(), _FakeResponse(200, body=b"done")

    monkeypatch.setattr(safe_fetch_mod.socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(safe_fetch_mod, "_send_fixed_ip_request", fake_send)

    response = safe_fetch_url("https://first.example/start")

    assert seen == [
        ("first.example", "93.184.216.34"),
        ("second.example", "93.184.216.35"),
    ]
    assert response.safe_final_url == "https://second.example/final"
    assert response.safe_final_ip == "93.184.216.35"
    assert response.safe_redirect_chain == [
        "https://first.example/start",
        "https://second.example/final",
    ]


def test_safe_fetch_rejects_private_redirect_target(monkeypatch) -> None:
    ip_map = {
        "first.example": "93.184.216.34",
        "internal.example": "127.0.0.1",
    }

    def fake_getaddrinfo(host: str, port: int | None):  # type: ignore[no-untyped-def]
        return _make_addrinfo(ip_map[host])

    def fake_send(target: ResolvedTarget, *, headers: dict, timeout: float):  # type: ignore[no-untyped-def]
        return _FakeSession(), _FakeResponse(
            302,
            headers={"Location": "http://internal.example/admin"},
        )

    monkeypatch.setattr(safe_fetch_mod.socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(safe_fetch_mod, "_send_fixed_ip_request", fake_send)

    with pytest.raises(UnsafeURLError):
        safe_fetch_url("https://first.example/start")


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("http://127.0.0.1", "private_ip_not_allowed"),
        ("http://localhost", "localhost_not_allowed"),
        ("http://example.com:22", "port_not_allowed"),
    ],
)
def test_validate_public_url_rejects_non_public_targets(url: str, reason: str, monkeypatch) -> None:
    monkeypatch.setattr(safe_fetch_mod.socket, "getaddrinfo", lambda host, port: _make_addrinfo("93.184.216.34"))

    with pytest.raises(UnsafeURLError) as exc_info:
        validate_public_url(url)

    assert exc_info.value.reason == reason
