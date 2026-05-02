# -*- coding: utf-8 -*-
"""Microsoft Entra External ID / Azure AD B2C JWT 認証ミドルウェア

NiceGUI / FastAPI の両方で利用できる認証モジュール。
Microsoft Entra External ID または Azure AD B2C の JWT トークンを検証し、
テナント情報を抽出する。
"""
import json
import logging
import os
import time
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# --- 環境変数 ---
EXTERNAL_TENANT_NAME = (
    os.environ.get("ENTRA_EXTERNAL_ID_TENANT_NAME")
    or os.environ.get("AZURE_B2C_TENANT_NAME", "")
)
EXTERNAL_CLIENT_ID = (
    os.environ.get("ENTRA_EXTERNAL_ID_CLIENT_ID")
    or os.environ.get("AZURE_B2C_CLIENT_ID", "")
)
EXTERNAL_POLICY = (
    os.environ.get("ENTRA_EXTERNAL_ID_POLICY")
    or os.environ.get("AZURE_B2C_POLICY", "B2C_1_signup_signin")
)
EXTERNAL_ISSUER = (
    os.environ.get("ENTRA_EXTERNAL_ID_ISSUER")
    or os.environ.get("AZURE_B2C_ISSUER", "")
)
EXTERNAL_DISCOVERY_URL = os.environ.get("ENTRA_EXTERNAL_ID_DISCOVERY_URL", "")
IDENTITY_MODE = os.environ.get("AUTH_IDENTITY_MODE", "entra_external_id")

# JWKS キャッシュ
_jwks_cache: Optional[Dict[str, Any]] = None
_jwks_cache_time: float = 0
_JWKS_CACHE_TTL = 3600  # 1 hour


def _get_openid_config_url() -> str:
    """Identity provider の OpenID Connect discovery URL"""
    if EXTERNAL_DISCOVERY_URL:
        return EXTERNAL_DISCOVERY_URL

    return (
        f"https://{EXTERNAL_TENANT_NAME}.b2clogin.com/"
        f"{EXTERNAL_TENANT_NAME}.onmicrosoft.com/{EXTERNAL_POLICY}/v2.0/.well-known/openid-configuration"
    )


def _fetch_jwks() -> Dict[str, Any]:
    """JWKS エンドポイントから公開鍵を取得（キャッシュ付き）"""
    global _jwks_cache, _jwks_cache_time

    now = time.time()
    if _jwks_cache and (now - _jwks_cache_time) < _JWKS_CACHE_TTL:
        return _jwks_cache

    try:
        config_url = _get_openid_config_url()
        config_resp = requests.get(config_url, timeout=10)
        config_resp.raise_for_status()
        jwks_uri = config_resp.json()["jwks_uri"]

        jwks_resp = requests.get(jwks_uri, timeout=10)
        jwks_resp.raise_for_status()
        _jwks_cache = jwks_resp.json()
        _jwks_cache_time = now
        return _jwks_cache
    except Exception as exc:
        logger.error("Failed to fetch JWKS: %s", exc)
        if _jwks_cache:
            return _jwks_cache
        raise


def verify_token(token: str) -> Dict[str, Any]:
    """JWT トークンを検証し、クレーム（ペイロード）を返す。

    検証失敗時は AuthError を送出する。
    """
    try:
        import jwt as pyjwt
        from jwt import PyJWKClient
    except ImportError:
        raise ImportError("PyJWT[crypto] が必要です: pip install PyJWT[crypto]")

    if not EXTERNAL_TENANT_NAME or not EXTERNAL_CLIENT_ID:
        raise AuthError("Microsoft Entra External ID / Azure AD B2C が設定されていません")

    jwks = _fetch_jwks()
    jwk_client = PyJWKClient.__new__(PyJWKClient)
    # マニュアルで JWKS をセット
    from jwt.api_jwk import PyJWKSet
    jwk_set = PyJWKSet.from_dict(jwks)

    # ヘッダーから kid を取得
    unverified_header = pyjwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    signing_key = None
    for key in jwk_set.keys:
        if key.key_id == kid:
            signing_key = key
            break

    if signing_key is None:
        raise AuthError("署名キーが見つかりません")

    issuer = EXTERNAL_ISSUER or (
        f"https://{EXTERNAL_TENANT_NAME}.b2clogin.com/{EXTERNAL_TENANT_NAME}.onmicrosoft.com/{EXTERNAL_POLICY}/v2.0"
    )

    payload = pyjwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=EXTERNAL_CLIENT_ID,
        issuer=issuer,
    )
    return payload


class AuthError(Exception):
    """認証エラー"""
    pass


def extract_tenant_id(claims: Dict[str, Any]) -> str:
    """JWT クレームからテナント ID を取得。
    カスタムクレーム extension_tenantId > oid > sub の優先順。
    """
    return (
        claims.get("extension_tenantId")
        or claims.get("oid")
        or claims.get("sub")
        or "unknown"
    )


def extract_user_info(claims: Dict[str, Any]) -> Dict[str, str]:
    """JWT クレームからユーザー情報を抽出"""
    return {
        "user_id": claims.get("oid") or claims.get("sub") or "",
        "email": claims.get("emails", [None])[0] if claims.get("emails") else claims.get("email", ""),
        "name": claims.get("name", ""),
        "tenant_id": extract_tenant_id(claims),
        "roles": claims.get("extension_roles", "user"),
        "identity_mode": IDENTITY_MODE,
    }
