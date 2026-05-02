"""HITL queue — markdown files in ~/.payments-agent/queue/.

Wraps solo-founder-os's HitlQueue. Reminder drafts above
$AMOUNT_AUTO_SEND threshold (default $25) MUST go through HITL.
Below that, gentle reminders can be set to auto-send via env flag.
"""
from __future__ import annotations
import pathlib

from solo_founder_os.hitl_queue import (
    APPROVED,
    HitlQueue,
    PENDING,
    REJECTED,
    SENT,
    make_basename,
    sanitize_filename_part,
)

from .types import ReminderDraft


def _default_queue_root() -> pathlib.Path:
    """Lazy resolution so tests' `monkeypatch.setattr(pathlib.Path, 'home',
    lambda: tmp_path)` actually takes effect — module-level constants
    capture home at import time, which is too early."""
    return pathlib.Path.home() / ".payments-agent" / "queue"


def _queue() -> HitlQueue:
    return HitlQueue.from_env("PAYMENTS_AGENT_QUEUE",
                                default=_default_queue_root())


def _render_markdown(draft: ReminderDraft, status: str) -> str:
    parts = [
        "---",
        "task: payment-reminder",
        f"invoice_id: {draft.invoice_id}",
        f"to: {draft.customer_email}",
        f"name: {draft.customer_name or '(anonymous)'}",
        f"severity: {draft.severity}",
        f"status: {status}",
        f"drafted_at: {draft.drafted_at.isoformat()}",
        "---",
        "",
        f"# {draft.subject}",
        "",
        f"**To:** {draft.customer_email}",
        f"**Severity:** {draft.severity}",
        "",
        "## Body",
        "",
        draft.body,
        "",
        "---",
        "",
        "## Audit",
        "",
        "### Prompt",
        "```",
        draft.raw_prompt[:2000] if draft.raw_prompt else "(template fallback)",
        "```",
        "",
        "### Response",
        f"`{(draft.raw_response or '')[:200]}`",
        "",
    ]
    return "\n".join(parts)


def queue_reminder(draft: ReminderDraft, *,
                     status: str = PENDING) -> pathlib.Path:
    q = _queue()
    body = _render_markdown(draft, status)
    base = make_basename([
        sanitize_filename_part(draft.invoice_id),
        sanitize_filename_part(draft.severity),
    ])
    return q.write(base, body, status=status)


def list_queue(*, status: str = PENDING) -> list[pathlib.Path]:
    return _queue().list(status=status)


__all__ = [
    "queue_reminder", "list_queue",
    "PENDING", "APPROVED", "REJECTED", "SENT",
]
