"""Tests for the API‑key security utilities.
These tests exercise the core ORM model and helper functions without requiring
the full HTTP stack. They use the SQLite fallback configured in
``db.connection`` when the ``DATABASE_URL`` env var is not set.
"""

import hashlib
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the project's DB utilities and the API‑key helpers.
from db.connection import Base
from services.api.security.api_key import (
    KEY_PREFIX,
    _hash_key,
    create_api_key,
    generate_plaintext_key,
)


# ---------------------------------------------------------------------------
# Fixture – a clean in‑memory SQLite DB for each test function.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session():
    # Ensure we use an isolated in‑memory DB.
    test_engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

# ---------------------------------------------------------------------------
# Helper – verify that a stored hash matches the plaintext key.
# ---------------------------------------------------------------------------
def assert_hash_matches(plain: str, stored_hash: str) -> bool:
    return stored_hash == hashlib.sha256(plain.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Test the creation function returns a plaintext key and stores only the hash.
# ---------------------------------------------------------------------------
def test_create_api_key_returns_plaintext_and_stores_hash(db_session):
    name = "unit‑test‑key"
    api_key_obj = create_api_key(db_session, name=name)

    # The function should attach the plaintext key as a private attribute.
    plaintext = getattr(api_key_obj, "_plain", None)
    assert plaintext is not None, "Plaintext key not attached"
    assert plaintext.startswith(KEY_PREFIX), "Plaintext key must start with the configured prefix"

    # The stored prefix should match the first 9 characters of the plaintext.
    expected_prefix = plaintext[: len(KEY_PREFIX)]
    assert api_key_obj.key_prefix == expected_prefix

    # The stored hash must correspond to the full plaintext.
    assert assert_hash_matches(plaintext, api_key_obj.key_hash)

    # Basic field checks.
    assert api_key_obj.name == name
    assert api_key_obj.is_active() is True
    assert isinstance(api_key_obj.created_at, datetime)

# ---------------------------------------------------------------------------
# Test that ``_hash_key`` produces the same SHA‑256 hash used by the model.
# ---------------------------------------------------------------------------
def test_hash_key_consistency():
    sample = generate_plaintext_key()
    direct = hashlib.sha256(sample.encode("utf-8")).hexdigest()
    assert _hash_key(sample) == direct

# ---------------------------------------------------------------------------
# Ensure that revoking a key makes ``is_active`` return ``False``.
# ---------------------------------------------------------------------------
def test_api_key_revocation(db_session):
    api_key_obj = create_api_key(db_session, name="revocation-test")
    # Revoke by setting ``revoked_at``.
    api_key_obj.revoked_at = datetime.utcnow()
    db_session.add(api_key_obj)
    db_session.commit()
    assert api_key_obj.is_active() is False
