"""Tests for stripe_provider + triage."""
from __future__ import annotations
import os
import pathlib
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from payments_agent.stripe_provider import (
    MockProvider,
    NotConfiguredError,
    StripeProvider,
    get_provider,
)
from payments_agent.triage import triage
from payments_agent.types import Customer, Invoice


# ──────────────────────────── providers ────────────────────────────


def test_mock_provider_returns_default_fixtures():
    p = MockProvider()
    invs = p.fetch_overdue_invoices()
    assert len(invs) == 3
    assert all(inv.is_overdue for inv in invs)
    severities = {inv.days_overdue for inv in invs}
    # Spans gentle / firm / final ranges
    assert any(d <= 7 for d in severities)
    assert any(8 <= d <= 30 for d in severities)
    assert any(d > 30 for d in severities)


def test_mock_provider_accepts_custom_invoices():
    custom = [Invoice(
        id="x", customer=Customer(id="c", email="z@x.com"),
        amount_due_cents=100, days_overdue=1,
    )]
    p = MockProvider(invoices=custom)
    assert p.fetch_overdue_invoices() == custom


def test_stripe_provider_without_key_raises(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    with pytest.raises(NotConfiguredError):
        StripeProvider()


def test_stripe_provider_v01_is_stub(monkeypatch):
    """v0.1 ships with the stub real provider — explicit
    NotImplementedError when called, not a silent return."""
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_x")
    p = StripeProvider()
    with pytest.raises(NotImplementedError):
        p.fetch_overdue_invoices()


def test_get_provider_falls_back_to_mock_without_key(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    p = get_provider()
    assert isinstance(p, MockProvider)


# ──────────────────────────── triage pipeline ────────────────────────────


def test_triage_processes_all_overdue(monkeypatch, tmp_path):
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = triage(provider=MockProvider())
    assert report.n_overdue == 3
    assert report.n_drafts_queued == 3
    severities = [d.severity for d in report.drafts]
    assert "gentle" in severities
    assert "firm" in severities
    assert "final" in severities


def test_triage_writes_to_pending_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    triage(provider=MockProvider())
    pending = tmp_path / ".payments-agent" / "queue" / "pending"
    files = list(pending.glob("*.md"))
    assert len(files) == 3
    # Frontmatter sanity
    body = files[0].read_text()
    assert "task: payment-reminder" in body
    assert "severity:" in body
    assert "## Body" in body


def test_triage_empty_invoices_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = triage(provider=MockProvider(invoices=[]))
    assert report.n_overdue == 0
    assert report.n_drafts_queued == 0
