"""Reminder-email drafter — Claude or template fallback.

Severity ladder picks tone:
  ≤7 days overdue   → gentle   ("just a heads up")
   8-30 days        → firm     ("this is now significantly overdue")
  >30 days          → final    ("we'll need to suspend service if not resolved")

Claude path uses solo_founder_os.AnthropicClient.messages_create_json
for guaranteed valid output. Template path is the fallback when
ANTHROPIC_API_KEY isn't set or the call fails.

Money is sensitive: the drafter NEVER claims a payment was received,
NEVER quotes a different amount than the invoice, and NEVER includes
a payment link not provided by the invoice. These are baked into the
system prompt as hard rules + asserted in tests.
"""
from __future__ import annotations
import pathlib
from datetime import datetime, timezone
from typing import Optional

from solo_founder_os.anthropic_client import (
    AnthropicClient,
    DEFAULT_HAIKU_MODEL,
)

from .types import Invoice, ReminderDraft


USAGE_LOG_PATH = (pathlib.Path.home()
                  / ".payments-agent" / "usage.jsonl")


def severity_for(days_overdue: int) -> str:
    """Pick severity label from days overdue. Pure function — same
    rule used by triage to gate HITL routing."""
    if days_overdue <= 7:
        return "gentle"
    if days_overdue <= 30:
        return "firm"
    return "final"


SYSTEM_PROMPT = """You are an indie founder writing a single payment-reminder \
email to a customer with an overdue invoice.

Hard rules — violating ANY of these means the draft is rejected:

1. NEVER thank the customer for a payment that hasn't happened. They are \
overdue. Do not say "thanks for your payment" or anything implying receipt.

2. State the EXACT amount and currency from the invoice. Do not round. \
Do not omit the currency.

3. State the EXACT number of days overdue. Don't say "a few days" when it's \
12. Don't soften "45 days" to "over a month".

4. Include the hosted invoice URL exactly as provided. NEVER invent a payment \
link or refer to one not in the input.

5. Match the severity tone:
   - gentle  (≤7 days):  conversational, "just a heads up", short
   - firm    (8-30):     direct but human, mention next-step consequences
   - final   (>30):      formal, mention service suspension as a next step

6. ≤90 words body. Subject ≤8 words. No emoji. No exclamation marks.

7. NEVER say "circling back", "touching base", "synergy", or generic SaaS \
billing-bot phrases. Sound like a founder, not a billing bot.

8. End with the founder's first name only — no signature block."""


DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["subject", "body"],
    "additionalProperties": False,
}


def _build_user_prompt(inv: Invoice, severity: str,
                         founder_name: str) -> str:
    name = inv.customer.name or "there"
    return (
        f"Severity: {severity}\n"
        f"Customer name: {name}\n"
        f"Customer email: {inv.customer.email}\n"
        f"Amount due: {inv.amount_due_dollars:.2f} {inv.currency.upper()}\n"
        f"Days overdue: {inv.days_overdue}\n"
        f"Invoice description: {inv.description or '(no description)'}\n"
        f"Hosted invoice URL: {inv.hosted_invoice_url or '(none — omit URL)'}\n"
        f"Founder first name: {founder_name}\n"
        "\n"
        "Draft the reminder now."
    )


def _template_fallback(inv: Invoice, severity: str,
                         founder_name: str) -> ReminderDraft:
    name = inv.customer.name.split()[0] if inv.customer.name else "there"
    amt = f"${inv.amount_due_dollars:.2f}"
    if severity == "gentle":
        body = (
            f"Hi {name},\n\n"
            f"Just a heads up — your invoice for {amt} is "
            f"{inv.days_overdue} days overdue. Pay here: "
            f"{inv.hosted_invoice_url or '(no URL on file)'}.\n\n"
            f"— {founder_name.split()[0] if founder_name else 'me'}"
        )
        subject = "Quick reminder"
    elif severity == "firm":
        body = (
            f"Hi {name},\n\n"
            f"Your invoice for {amt} is now {inv.days_overdue} days overdue. "
            f"Please pay here: {inv.hosted_invoice_url or '(no URL on file)'}. "
            "If there's a billing issue, reply and I'll fix it.\n\n"
            f"— {founder_name.split()[0] if founder_name else 'me'}"
        )
        subject = "Overdue invoice — please pay"
    else:  # final
        body = (
            f"Hi {name},\n\n"
            f"Your invoice for {amt} is {inv.days_overdue} days overdue. "
            "If we don't see payment this week we'll need to suspend "
            f"service. Pay here: "
            f"{inv.hosted_invoice_url or '(no URL on file)'}.\n\n"
            f"— {founder_name.split()[0] if founder_name else 'me'}"
        )
        subject = "Final notice — service suspension"
    return ReminderDraft(
        invoice_id=inv.id,
        customer_email=inv.customer.email,
        customer_name=inv.customer.name,
        subject=subject,
        body=body,
        severity=severity,
        drafted_at=datetime.now(timezone.utc),
        raw_prompt="(template mode — no API key)",
        raw_response="",
    )


def draft_reminder(
    invoice: Invoice,
    *,
    founder_name: str = "Alex",
    model: str = DEFAULT_HAIKU_MODEL,
    client: Optional[AnthropicClient] = None,
) -> ReminderDraft:
    """One Claude call per invoice. Always returns a ReminderDraft —
    falls back to template on missing API key, error, or empty output."""
    severity = severity_for(invoice.days_overdue)

    if client is None:
        client = AnthropicClient(usage_log_path=USAGE_LOG_PATH)

    if not client.configured:
        return _template_fallback(invoice, severity, founder_name)

    user = _build_user_prompt(invoice, severity, founder_name)
    obj, err = client.messages_create_json(
        schema=DRAFT_SCHEMA,
        model=model,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    if err is not None:
        d = _template_fallback(invoice, severity, founder_name)
        d.raw_response = f"(LLM error, fell back: {err})"
        _log_reflection("PARTIAL", f"draft Claude error: {str(err)[:200]}")
        return d

    subject = (obj.get("subject") or "").strip()
    body = (obj.get("body") or "").strip()
    if not subject or not body:
        d = _template_fallback(invoice, severity, founder_name)
        d.raw_response = "(LLM returned empty subject/body, fell back)"
        _log_reflection("PARTIAL", "Claude returned empty draft")
        return d

    # L3 record_example for ICPL / skill distillation later.
    try:
        from solo_founder_os import record_example
        record_example(
            "draft-payment-reminder",
            inputs={
                "severity": severity,
                "days_overdue": invoice.days_overdue,
                "amount_dollars": round(invoice.amount_due_dollars, 2),
                "currency": invoice.currency,
            },
            output=f"Subject: {subject}\n\n{body}",
            note="LLM-drafted, pre-HITL",
        )
    except Exception:
        pass

    return ReminderDraft(
        invoice_id=invoice.id,
        customer_email=invoice.customer.email,
        customer_name=invoice.customer.name,
        subject=subject,
        body=body,
        severity=severity,
        drafted_at=datetime.now(timezone.utc),
        raw_prompt=user,
        raw_response=f"(structured-output JSON: {obj})",
    )


def _log_reflection(outcome: str, signal: str) -> None:
    """L1 reflexion sink — best-effort, never raises into draft path."""
    try:
        from solo_founder_os import log_outcome
        log_outcome(
            ".payments-agent",
            "draft_payment_reminder",
            outcome,
            signal,
            skip_reflection=True,
        )
    except Exception:
        pass
