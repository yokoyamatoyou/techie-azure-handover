from __future__ import annotations

import os
import socket
import ipaddress
from dataclasses import asdict, dataclass
from typing import Optional, Sequence
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.poolmanager import PoolKey, _default_key_normalizer

from core.config import config
from core.rate_limiter import rate_limiter

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443, 8080, 8443}
DEFAULT_MAX_BYTES = int(os.getenv("MAX_FETCH_BYTES", str(10 * 1024 * 1024)))
DEFAULT_TIMEOUT = float(os.getenv("FETCH_TIMEOUT", str(config.TIMEOUT_LONG)))
MAX_REDIRECTS = int(os.getenv("FETCH_MAX_REDIRECTS", "5"))


class SafeFetchError(Exception):
    pass


class UnsafeURLError(SafeFetchError):
    def __init__(self, url: str, reason: str):
        super().__init__(f"UNSAFE_URL: {reason}")
        self.url = url
        self.reason = reason


class ContentTooLargeError(SafeFetchError):
    def __init__(self, url: str, size_bytes: int, max_bytes: int):
        super().__init__(f"CONTENT_TOO_LARGE: {size_bytes} > {max_bytes}")
        self.url = url
        self.size_bytes = size_bytes
        self.max_bytes = max_bytes


class TooManyRedirectsError(SafeFetchError):
    def __init__(self, url: str, max_redirects: int):
        super().__init__(f"TOO_MANY_REDIRECTS: limit={max_redirects}")
        self.url = url
        self.max_redirects = max_redirects


@dataclass(frozen=True)
class ResolvedTarget:
    original_url: str
    normalized_url: str
    scheme: str
    hostname: str
    port: int
    connect_ip: str
    resolved_ips: tuple[str, ...]

    def to_metadata(self) -> dict:
        return asdict(self)


def _is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(
        [
            addr.is_private,
            addr.is_loopback,
            addr.is_link_local,
            addr.is_multicast,
            addr.is_reserved,
            addr.is_unspecified,
        ]
    )


def _resolve_host(host: str) -> tuple[str, ...]:
    ips: list[str] = []
    seen: set[str] = set()
    try:
        for info in socket.getaddrinfo(host, None):
            if not info or not info[4]:
                continue
            ip = info[4][0]
            if not ip or ip in seen:
                continue
            seen.add(ip)
            ips.append(ip)
    except Exception:
        return ()
    return tuple(ips)


def _normalize_hostname(hostname: str) -> str:
    return hostname.strip().rstrip(".").lower()


def _normalize_url(url: str, *, scheme: str, hostname: str, port: int) -> str:
    parsed = urlparse(url)
    netloc = hostname
    default_port = 443 if scheme == "https" else 80
    if port != default_port:
        netloc = f"{netloc}:{port}"
    normalized = parsed._replace(scheme=scheme, netloc=netloc, fragment="")
    return normalized.geturl()


def _pick_connect_ip(ips: Sequence[str]) -> str:
    ipv4 = [ip for ip in ips if ":" not in ip]
    return ipv4[0] if ipv4 else ips[0]


def resolve_public_target(url: str) -> ResolvedTarget:
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(url, "unsupported_scheme")
    if not parsed.hostname:
        raise UnsafeURLError(url, "missing_hostname")
    if parsed.username or parsed.password:
        raise UnsafeURLError(url, "userinfo_not_allowed")

    host = _normalize_hostname(parsed.hostname)
    if host == "localhost" or host.endswith(".localhost"):
        raise UnsafeURLError(url, "localhost_not_allowed")

    try:
        port = parsed.port or (443 if scheme == "https" else 80)
    except ValueError as exc:
        raise UnsafeURLError(url, f"invalid_port:{exc}") from exc
    if port not in ALLOWED_PORTS:
        raise UnsafeURLError(url, "port_not_allowed")

    resolved_ips: tuple[str, ...]
    try:
        ipaddress.ip_address(host)
        if _is_private_ip(host):
            raise UnsafeURLError(url, "private_ip_not_allowed")
        resolved_ips = (host,)
    except ValueError:
        resolved_ips = _resolve_host(host)
        if not resolved_ips:
            raise UnsafeURLError(url, "dns_resolution_failed")
        for ip in resolved_ips:
            if _is_private_ip(ip):
                raise UnsafeURLError(url, "private_ip_not_allowed")

    normalized_url = _normalize_url(url, scheme=scheme, hostname=host, port=port)
    return ResolvedTarget(
        original_url=url,
        normalized_url=normalized_url,
        scheme=scheme,
        hostname=host,
        port=port,
        connect_ip=_pick_connect_ip(resolved_ips),
        resolved_ips=tuple(resolved_ips),
    )


def validate_public_url(url: str) -> ResolvedTarget:
    """Public helper for validating user-supplied fetch targets."""
    return resolve_public_target(url)


class _FixedIPMixin:
    def __init__(self, *args, fixed_ip: str, **kwargs):
        self._fixed_ip = fixed_ip
        super().__init__(*args, **kwargs)

    def _new_conn(self):  # type: ignore[override]
        target_host = self._fixed_ip or self._dns_host
        try:
            sock = socket.create_connection(
                (target_host, self.port),
                self.timeout,
                source_address=self.source_address,
            )
        except socket.gaierror as exc:
            raise OSError(f"fixed_ip_resolution_failed:{target_host}") from exc
        if self.socket_options:
            for opt in self.socket_options:
                sock.setsockopt(*opt)
        return sock


class _FixedIPHTTPConnection(_FixedIPMixin, HTTPConnection):
    pass


class _FixedIPHTTPSConnection(_FixedIPMixin, HTTPSConnection):
    pass


class _FixedIPHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = _FixedIPHTTPConnection


class _FixedIPHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _FixedIPHTTPSConnection


class _FixedIPPoolManager(PoolManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pool_classes_by_scheme = {
            "http": _FixedIPHTTPConnectionPool,
            "https": _FixedIPHTTPSConnectionPool,
        }
        self.key_fn_by_scheme = {
            "http": self._fixed_ip_key_fn,
            "https": self._fixed_ip_key_fn,
        }

    @staticmethod
    def _fixed_ip_key_fn(request_context: dict) -> PoolKey:
        normalized_context = dict(request_context)
        normalized_context.pop("fixed_ip", None)
        return _default_key_normalizer(PoolKey, normalized_context)


class _FixedIPHTTPAdapter(HTTPAdapter):
    def __init__(self, target: ResolvedTarget):
        self._target = target
        super().__init__()

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs = dict(pool_kwargs)
        pool_kwargs["fixed_ip"] = self._target.connect_ip
        self.poolmanager = _FixedIPPoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )


def _build_fixed_ip_session(target: ResolvedTarget) -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    adapter = _FixedIPHTTPAdapter(target)
    session.mount(f"{target.scheme}://", adapter)
    return session


def _send_fixed_ip_request(
    target: ResolvedTarget,
    *,
    headers: dict,
    timeout: float,
) -> tuple[requests.Session, requests.Response]:
    session = _build_fixed_ip_session(target)
    response = session.get(
        target.normalized_url,
        headers=headers,
        timeout=timeout,
        stream=True,
        allow_redirects=False,
    )
    return session, response


def resolve_safe_redirect_chain(
    url: str,
    *,
    headers: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = MAX_REDIRECTS,
) -> list[ResolvedTarget]:
    request_headers = dict(headers or {})
    if "User-Agent" not in request_headers:
        request_headers["User-Agent"] = config.USER_AGENT

    current_url = url
    chain: list[ResolvedTarget] = []

    for redirect_count in range(max_redirects + 1):
        target = resolve_public_target(current_url)
        chain.append(target)
        rate_limiter.wait(target.normalized_url)
        session, response = _send_fixed_ip_request(target, headers=request_headers, timeout=timeout)
        try:
            location = response.headers.get("Location")
            if response.status_code in (301, 302, 303, 307, 308) and location:
                if redirect_count >= max_redirects:
                    raise TooManyRedirectsError(target.normalized_url, max_redirects)
                current_url = urljoin(target.normalized_url, location)
                continue
            break
        finally:
            response.close()
            session.close()

    return chain


def safe_fetch_url(
    url: str,
    *,
    headers: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_redirects: int = MAX_REDIRECTS,
) -> requests.Response:
    request_headers = dict(headers or {})
    if "User-Agent" not in request_headers:
        request_headers["User-Agent"] = config.USER_AGENT

    current_url = url
    redirect_chain: list[str] = []
    resolved_targets: list[ResolvedTarget] = []
    response: Optional[requests.Response] = None
    final_target: Optional[ResolvedTarget] = None

    for redirect_count in range(max_redirects + 1):
        target = resolve_public_target(current_url)
        final_target = target
        resolved_targets.append(target)
        redirect_chain.append(target.normalized_url)
        rate_limiter.wait(target.normalized_url)
        session, response = _send_fixed_ip_request(target, headers=request_headers, timeout=timeout)

        location = response.headers.get("Location")
        if response.status_code in (301, 302, 303, 307, 308) and location:
            response.close()
            session.close()
            if redirect_count >= max_redirects:
                raise TooManyRedirectsError(target.normalized_url, max_redirects)
            current_url = urljoin(target.normalized_url, location)
            continue
        break

    if response is None or final_target is None:
        raise SafeFetchError("failed_to_fetch")

    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise ContentTooLargeError(final_target.normalized_url, int(content_length), max_bytes)
        except ValueError:
            pass

    content = bytearray()
    try:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            content += chunk
            if len(content) > max_bytes:
                raise ContentTooLargeError(final_target.normalized_url, len(content), max_bytes)
    finally:
        response.close()
        session.close()

    response._content = bytes(content)
    try:
        response.encoding = response.apparent_encoding or response.encoding
    except Exception:
        pass
    response.safe_content_size_bytes = len(content)
    response.safe_final_url = final_target.normalized_url
    response.safe_final_ip = final_target.connect_ip
    response.safe_redirect_chain = list(redirect_chain)
    response.safe_redirect_count = max(0, len(redirect_chain) - 1)
    response.safe_resolved_targets = [target.to_metadata() for target in resolved_targets]
    response.safe_resolved_ips = list(final_target.resolved_ips)
    return response
