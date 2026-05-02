"""Provider abstraction — real Stripe vs mock.

Why this exists: a solo founder may not have a Stripe key configured
yet, or may want to dry-run the agent before wiring billing. The
abstract Provider lets the rest of the agent (drafter, triage, queue)
operate on Invoice objects without caring where they came from.

Real Stripe wiring is a stub for v0.1 — when STRIPE_API_KEY is set
we'd call `stripe.Invoice.list(status='open')`, but that's a follow-
up. For now the real provider just raises a clear NotConfigured
error so the operator knows to fall back to mock.
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from .types import Customer, Invoice


class StripeProvider:
    """Real Stripe API. v0.1: stubbed — raises if used.

    To enable in v0.2: `pip install stripe`, set STRIPE_API_KEY,
    swap the body of fetch_overdue_invoices for `stripe.Invoice.list(...)`.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("STRIPE_API_KEY")
        if not self.api_key:
            raise NotConfiguredError(
                "STRIPE_API_KEY not set. Use MockProvider() for dev/dry-run, "
                "or set the env var.",
            )

    def fetch_overdue_invoices(self) -> list[Invoice]:
        # Real implementation would do:
        #   import stripe
        #   stripe.api_key = self.api_key
        #   raw = stripe.Invoice.list(status="open", limit=100)
        #   return [_to_invoice(r) for r in raw.auto_paging_iter()]
        raise NotImplementedError(
            "v0.1 ships with the mock provider. Real Stripe wiring "
            "lands in v0.2 once the agent has been validated against "
            "fixture data.",
        )


class MockProvider:
    """Drop-in mock — returns a hardcoded set of overdue invoices.

    Use for dev, dry-run, tests, and the "I don't have Stripe yet"
    onboarding path. Each invoice carries `days_overdue` so the
    drafter can pick severity (gentle / firm / final) without
    further computation.
    """

    def __init__(self, invoices: Optional[list[Invoice]] = None):
        self._invoices = invoices if invoices is not None else _default_fixtures()

    def fetch_overdue_invoices(self) -> list[Invoice]:
        return list(self._invoices)


class NotConfiguredError(RuntimeError):
    """Raised when StripeProvider is constructed without an API key."""


def get_provider() -> object:
    """Return the right provider for the current env. Caller treats
    both as duck-typed (just calls fetch_overdue_invoices)."""
    if os.getenv("STRIPE_API_KEY"):
        try:
            return StripeProvider()
        except NotConfiguredError:
            return MockProvider()
    return MockProvider()


# ──────────────────────────── fixtures ────────────────────────────


def _default_fixtures() -> list[Invoice]:
    """Three plausible overdue invoices for dev / demo / tests.
    Spans the gentle / firm / final severity bands."""
    now = datetime.now(timezone.utc)
    return [
        Invoice(
            id="in_test_001",
            customer=Customer(
                id="cus_test_001",
                email="alice@example.com",
                name="Alice Founder",
            ),
            amount_due_cents=4900,  # $49
            currency="usd",
            status="open",
            due_date=now - timedelta(days=3),
            description="VibeXForge Pro — Apr 2026",
            hosted_invoice_url="https://invoice.stripe.com/x/01",
            days_overdue=3,
        ),
        Invoice(
            id="in_test_002",
            customer=Customer(
                id="cus_test_002",
                email="bob@example.com",
                name="Bob Builder",
            ),
            amount_due_cents=29900,  # $299
            currency="usd",
            status="open",
            due_date=now - timedelta(days=12),
            description="VibeXForge Team — Apr 2026",
            hosted_invoice_url="https://invoice.stripe.com/x/02",
            days_overdue=12,
        ),
        Invoice(
            id="in_test_003",
            customer=Customer(
                id="cus_test_003",
                email="carol@example.com",
                name=None,  # tests the "no name" path
            ),
            amount_due_cents=9900,  # $99
            currency="usd",
            status="open",
            due_date=now - timedelta(days=45),
            description="VibeXForge Pro — Mar 2026",
            hosted_invoice_url="https://invoice.stripe.com/x/03",
            days_overdue=45,
        ),
    ]
