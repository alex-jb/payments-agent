"""Stripe-shaped types — works with a real Stripe SDK or the mock provider.

Field names match Stripe's REST API where possible (id, customer,
amount_due, currency, due_date, status) so wiring up the real
provider later is a 1-line swap.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Customer:
    """Subset of Stripe Customer fields — only what we need to draft email."""
    id: str
    email: str
    name: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Invoice:
    """Subset of Stripe Invoice fields."""
    id: str
    customer: Customer
    amount_due_cents: int
    currency: str = "usd"
    status: str = "open"           # draft | open | paid | uncollectible | void
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    days_overdue: int = 0          # computed by the provider, not Stripe-native

    @property
    def amount_due_dollars(self) -> float:
        return self.amount_due_cents / 100.0

    @property
    def is_overdue(self) -> bool:
        return self.status == "open" and self.days_overdue > 0


@dataclass
class ReminderDraft:
    """One Claude-drafted (or template fallback) reminder email."""
    invoice_id: str
    customer_email: str
    customer_name: Optional[str]
    subject: str
    body: str
    severity: str  # "gentle" | "firm" | "final"
    drafted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    raw_prompt: str = ""
    raw_response: str = ""
