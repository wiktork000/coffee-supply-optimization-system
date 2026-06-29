"""Unit tests for coffee_manager.auth helpers (no DB needed)."""

import time
import uuid

import pytest
from fastapi import HTTPException
from jose import jwt

from coffee_manager import auth as auth_module
from coffee_manager.config import settings


def test_hash_and_verify_password_roundtrip():
    h = auth_module.hash_password("hunter2")
    assert h != "hunter2"
    assert auth_module.verify_password("hunter2", h) is True
    assert auth_module.verify_password("wrong", h) is False


def test_create_and_decode_access_token():
    uid = str(uuid.uuid4())
    token = auth_module.create_access_token(uid, "coordinator")
    payload = auth_module.decode_token(token)
    assert payload["sub"] == uid
    assert payload["role"] == "coordinator"
    assert "exp" in payload


def test_decode_token_rejects_invalid():
    with pytest.raises(HTTPException) as ei:
        auth_module.decode_token("not-a-valid-jwt")
    assert ei.value.status_code == 401


def test_decode_token_rejects_wrong_signature():
    # Forge a token with a different secret.
    bogus = jwt.encode(
        {"sub": "x", "role": "coordinator", "exp": int(time.time()) + 60},
        "different-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException):
        auth_module.decode_token(bogus)


def test_generate_api_key_shape():
    raw, prefix, key_hash = auth_module.generate_api_key()
    assert raw.startswith("cof_")
    assert len(prefix) == 16
    assert raw[:16] == prefix
    # Hash is bcrypt and verifies against raw.
    assert auth_module.verify_password(raw, key_hash) is True
    # Two calls yield distinct keys.
    raw2, _, _ = auth_module.generate_api_key()
    assert raw != raw2
