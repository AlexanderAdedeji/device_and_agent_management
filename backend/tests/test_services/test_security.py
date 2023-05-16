from datetime import timedelta
from backend.app.services.security import (
    generate_reset_token,
    decode_reset_token,
    verify_api_key,
    get_api_key_hash,
)
from backend.tests.utils import random_email
import pytest
from itsdangerous.exc import BadSignature
from passlib.exc import InvalidHashError


def test_generate_and_decode_reset_token():
    email = random_email()
    assert decode_reset_token(generate_reset_token(email)) == email


def test_invalid_reset_token_throws_exception():
    with pytest.raises(BadSignature):
        assert decode_reset_token("invalid reset token")


def test_expired_reset_token_doesnt_work():
    with pytest.raises(ValueError):
        token = generate_reset_token(random_email(), expires_delta=timedelta(0))
        decode_reset_token(token)


def test_api_key_hash_is_consistent():
    api_key = "some-api-key"
    original_api_key_hash = get_api_key_hash(api_key)
    assert all(
        original_api_key_hash == api_key_hash
        for api_key_hash in [get_api_key_hash(api_key) for _ in range(5)]
    )


def test_verify_api_key_with_valid_hash_returns_true():
    api_key = "some-api-key"
    assert verify_api_key(api_key, get_api_key_hash(api_key))


def test_verify_api_key_with_invalid_hash_returns_false():
    assert not verify_api_key("some-api-key", "some-invalid-bcrypt-hash")
