"""Unit tests for the in-memory session ownership store (E3/FR-013..FR-021)."""

from __future__ import annotations

import pytest

from healthcare_support.data import session_access
from healthcare_support.data.session_access import AccessDecision, SessionAccessStore


@pytest.fixture
def store() -> SessionAccessStore:
    return SessionAccessStore()


class TestCreate:
    def test_create_returns_opaque_proof_and_stores_only_digest(
        self, store: SessionAccessStore
    ) -> None:
        proof = store.create("conv-1")
        assert proof
        record = store._records["conv-1"]
        assert record.proof_digest != proof
        assert len(record.proof_digest) == 64
        assert record.proof_digest == record.proof_digest.lower()
        assert set(record.proof_digest) <= set("0123456789abcdef")
        assert record.active is True
        assert record.created_at.tzinfo is not None

    def test_create_is_active_and_verifies(self, store: SessionAccessStore) -> None:
        proof = store.create("conv-1")
        assert store.is_active("conv-1") is True
        assert store.verify("conv-1", proof) == AccessDecision.GRANTED

    def test_create_rejects_duplicate_active_session(self, store: SessionAccessStore) -> None:
        store.create("conv-1")
        with pytest.raises(ValueError):
            store.create("conv-1")


class TestVerify:
    def test_missing_proof(self, store: SessionAccessStore) -> None:
        store.create("conv-1")
        assert store.verify("conv-1", None) == AccessDecision.MISSING

    def test_malformed_proof(self, store: SessionAccessStore) -> None:
        store.create("conv-1")
        assert store.verify("conv-1", "short") == AccessDecision.MALFORMED

    def test_unknown_identifier(self, store: SessionAccessStore) -> None:
        assert store.verify("nope", "a" * 43) == AccessDecision.UNKNOWN

    def test_invalid_proof(self, store: SessionAccessStore) -> None:
        store.create("conv-1")
        assert store.verify("conv-1", "b" * 43) == AccessDecision.INVALID

    def test_cross_session_proof_is_invalid(self, store: SessionAccessStore) -> None:
        store.create("conv-1")
        proof_b = store.create("conv-2")
        assert store.verify("conv-1", proof_b) == AccessDecision.INVALID

    def test_inactive_session_is_denied(self, store: SessionAccessStore) -> None:
        proof = store.create("conv-1")
        store.deactivate("conv-1")
        assert store.is_active("conv-1") is False
        assert store.verify("conv-1", proof) == AccessDecision.INACTIVE

    def test_uses_constant_time_comparison(
        self, store: SessionAccessStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[tuple[str, str]] = []
        real_compare = session_access.hmac.compare_digest

        def spy(left: str, right: str) -> bool:
            calls.append((left, right))
            return real_compare(left, right)

        monkeypatch.setattr(session_access.hmac, "compare_digest", spy)
        proof = store.create("conv-1")
        assert store.verify("conv-1", proof) == AccessDecision.GRANTED
        assert calls, "verify must compare digests with hmac.compare_digest"


class TestRotateDeactivateClear:
    def test_rotate_invalidates_prior_proof(self, store: SessionAccessStore) -> None:
        old = store.create("conv-1")
        new = store.rotate("conv-1")
        assert new != old
        assert store.verify("conv-1", old) == AccessDecision.INVALID
        assert store.verify("conv-1", new) == AccessDecision.GRANTED

    def test_rotate_unknown_identifier_raises(self, store: SessionAccessStore) -> None:
        with pytest.raises(KeyError):
            store.rotate("missing")

    def test_clear_removes_all_records(self, store: SessionAccessStore) -> None:
        store.create("conv-1")
        store.clear()
        assert store.is_active("conv-1") is False
