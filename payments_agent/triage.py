"""Top-level pipeline — fetch overdue invoices, draft, queue.

Run via `payments-agent triage` or `python -m payments_agent triage`.
Returns a TriageReport for tests / introspection.
"""
from __future__ import annotations
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .drafter import draft_reminder
from .queue import queue_reminder
from .stripe_provider import get_provider
from .types import Invoice, ReminderDraft


@dataclass
class TriageReport:
    started_at: str
    n_overdue: int = 0
    n_drafts_queued: int = 0
    drafts: list[ReminderDraft] = field(default_factory=list)


def triage(
    *,
    founder_name: str = "Alex",
    provider: Optional[object] = None,
    queue_dir: Optional[pathlib.Path] = None,
) -> TriageReport:
    """Walk all overdue invoices, draft a reminder per, queue each."""
    started = datetime.now(timezone.utc).isoformat()
    report = TriageReport(started_at=started)

    if provider is None:
        provider = get_provider()

    invoices: list[Invoice] = provider.fetch_overdue_invoices()
    report.n_overdue = len(invoices)

    for inv in invoices:
        draft = draft_reminder(inv, founder_name=founder_name)
        report.drafts.append(draft)
        try:
            queue_reminder(draft)
            report.n_drafts_queued += 1
        except Exception:
            # Queue write failure shouldn't crash triage — the draft
            # is preserved in the report for rerun.
            pass

    return report
