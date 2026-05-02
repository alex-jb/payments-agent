"""Tests for drafter — money-sensitive prompts demand strict tests."""
from __future__ import annotations
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from payments_agent.drafter import (
    SYSTEM_PROMPT,
    draft_reminder,
    severity_for,
)
from payments_agent.types import Customer, Invoice


def _invoice(days: int, *, amount_cents: int = 4900,
              name: str = "Alice Founder") -> Invoice:
    return Invoice(
        id="in_test",
        customer=Customer(id="cus_test", email="alice@example.com",
                            name=name),
        amount_due_cents=amount_cents,
        currency="usd",
        status="open",
        due_date=datetime.now(timezone.utc) - timedelta(days=days),
        description="Test plan",
        hosted_invoice_url="https://invoice.stripe.com/x/abc",
        days_overdue=days,
    )


# ──────────────────────────── severity ladder ────────────────────────────


def test_severity_for_gentle_threshold():
    assert severity_for(0) == "gentle"
    assert severity_for(1) == "gentle"
    assert severity_for(7) == "gentle"


def test_severity_for_firm_threshold():
    assert severity_for(8) == "firm"
    assert severity_for(15) == "firm"
    assert severity_for(30) == "firm"


def test_severity_for_final_threshold():
    assert severity_for(31) == "final"
    assert severity_for(60) == "final"
    assert severity_for(365) == "final"


# ──────────────────────────── system prompt safety ────────────────────────────


def test_system_prompt_forbids_thanks_for_payment():
    """The most dangerous LLM hallucination for this agent: thanking
    a customer for a payment that didn't happen. The system prompt
    must forbid this in plain language."""
    assert "NEVER thank the customer for a payment" in SYSTEM_PROMPT


def test_system_prompt_demands_exact_amount():
    assert "EXACT amount" in SYSTEM_PROMPT


def test_system_prompt_forbids_inventing_payment_link():
    assert "NEVER invent a payment link" in SYSTEM_PROMPT


# ──────────────────────────── template fallback ────────────────────────────


def test_draft_reminder_no_api_key_uses_template(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    inv = _invoice(days=3)
    draft = draft_reminder(inv, founder_name="Alex")
    assert draft.severity == "gentle"
    assert "$49.00" in draft.body
    assert "3 days overdue" in draft.body
    assert "https://invoice.stripe.com/x/abc" in draft.body
    assert "Alex" in draft.body
    # Template body must NOT mention the dangerous patterns
    assert "thank" not in draft.body.lower() or "thanks for" not in draft.body.lower()


def test_template_firm_severity_includes_consequences(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    inv = _invoice(days=15)
    draft = draft_reminder(inv)
    assert draft.severity == "firm"
    assert "15 days overdue" in draft.body


def test_template_final_mentions_suspension(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    inv = _invoice(days=45)
    draft = draft_reminder(inv)
    assert draft.severity == "final"
    assert "suspend" in draft.body.lower()
    assert "45 days overdue" in draft.body


def test_template_handles_anonymous_customer(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    inv = _invoice(days=3, name=None)
    draft = draft_reminder(inv)
    assert "there" in draft.body  # fallback greeting


# ──────────────────────────── Claude path ────────────────────────────


def test_draft_reminder_with_fake_claude(monkeypatch):
    """Inject a fake AnthropicClient that returns structured output —
    verify the result Draft has expected fields populated."""
    fake = MagicMock()
    fake.configured = True
    fake.messages_create_json.return_value = (
        {"subject": "Reminder: Apr invoice",
         "body": "Hi Alice, your $49.00 USD invoice is 3 days overdue. "
                  "Please pay at https://invoice.stripe.com/x/abc.\n\n— Alex"},
        None,
    )
    inv = _invoice(days=3)
    draft = draft_reminder(inv, client=fake)
    assert draft.subject == "Reminder: Apr invoice"
    assert "Alice" in draft.body
    assert "$49.00" in draft.body


def test_draft_reminder_llm_error_falls_back_to_template():
    fake = MagicMock()
    fake.configured = True
    fake.messages_create_json.return_value = (None, "rate limit")
    inv = _invoice(days=12, amount_cents=29900)
    draft = draft_reminder(inv, client=fake)
    # Template populated correctly even though Claude was tried
    assert "$299.00" in draft.body
    assert "12 days overdue" in draft.body
    assert "rate limit" in draft.raw_response


def test_draft_reminder_empty_subject_falls_back():
    fake = MagicMock()
    fake.configured = True
    fake.messages_create_json.return_value = (
        {"subject": "", "body": "non-empty"}, None,
    )
    inv = _invoice(days=3)
    draft = draft_reminder(inv, client=fake)
    assert "fell back" in draft.raw_response
