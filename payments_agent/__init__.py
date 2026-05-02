"""payments-agent — Solo Founder OS agent #11.

The 7th canonical layer of a one-person-company stack: monetization.
Drafts overdue-invoice reminder emails for paying customers; queues
high-value reminders for HITL approval before send.

Stripe-shaped data model with a pluggable provider so the agent
works WITHOUT a Stripe key (mock provider for dev / tests / dry-run)
and seamlessly switches to a real Stripe API call when configured.

Built on solo-founder-os v0.20+ for HitlQueue / AnthropicClient /
log_outcome / record_example primitives.
"""
__version__ = "0.1.0"

from .types import Customer, Invoice, ReminderDraft
from .stripe_provider import StripeProvider, MockProvider, get_provider
from .drafter import draft_reminder
from .queue import queue_reminder, list_queue
from .triage import triage

__all__ = [
    "__version__",
    "Customer", "Invoice", "ReminderDraft",
    "StripeProvider", "MockProvider", "get_provider",
    "draft_reminder",
    "queue_reminder", "list_queue",
    "triage",
]
