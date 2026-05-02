"""payments-agent CLI."""
from __future__ import annotations
import argparse
import sys

from .triage import triage as run_triage
from .queue import list_queue, PENDING, APPROVED


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="payments-agent",
        description="Solo Founder OS agent #11 — overdue invoice "
                     "reminders with HITL gating.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_triage = sub.add_parser(
        "triage",
        help="Fetch overdue invoices, draft a reminder per, queue each.",
    )
    p_triage.add_argument("--founder-name", default="Alex",
                            help="Name to sign reminders with.")
    p_triage.set_defaults(func=cmd_triage)

    p_q = sub.add_parser("queue-status",
                          help="Show pending / approved counts.")
    p_q.set_defaults(func=cmd_queue_status)

    args = p.parse_args(argv)
    return args.func(args)


def cmd_triage(args: argparse.Namespace) -> int:
    report = run_triage(founder_name=args.founder_name)
    print(f"  ✓ {report.n_overdue} overdue invoice(s) seen, "
          f"{report.n_drafts_queued} reminder(s) queued",
          file=sys.stderr)
    for d in report.drafts:
        print(f"    - {d.severity:6}  {d.invoice_id}  "
              f"→ {d.customer_email}", file=sys.stderr)
    return 0


def cmd_queue_status(args: argparse.Namespace) -> int:
    pending = list_queue(status=PENDING)
    approved = list_queue(status=APPROVED)
    print(f"  pending:  {len(pending)}", file=sys.stderr)
    print(f"  approved: {len(approved)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
