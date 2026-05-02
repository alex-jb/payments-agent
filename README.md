# payments-agent

Solo Founder OS agent #11 — overdue-invoice reminder drafter with HITL gating.

The 7th canonical layer of a one-person-company stack: monetization. Drafts
reminder emails for overdue Stripe invoices, picks tone by severity (gentle /
firm / final), queues every draft for human approval before send.

Built on [solo-founder-os](https://github.com/alex-jb/solo-founder-os) — uses
its `HitlQueue`, `AnthropicClient`, `log_outcome`, and `record_example`
primitives.

## Why money is special

The agent's system prompt has hard rules other agents don't need:

- NEVER thank a customer for a payment that didn't happen.
- State the EXACT amount and currency from the invoice. No rounding.
- State the EXACT number of days overdue.
- NEVER invent a payment link.

These are asserted in tests so a future prompt rewrite can't drift them away.

## Install

```bash
pip install payments-agent
```

Optional Stripe wiring (v0.2):
```bash
pip install 'payments-agent[stripe]'
export STRIPE_API_KEY=sk_live_...
```

Without `STRIPE_API_KEY`, the agent uses `MockProvider` with three fixture
invoices — useful for dev, demos, dry-runs, and the "I don't have Stripe
yet" onboarding path.

## Usage

```bash
# Dry-run with mock invoices, queue 3 reminders to ~/.payments-agent/queue/pending/
payments-agent triage

# Show queue counts
payments-agent queue-status

# Approve / reject manually:
mv ~/.payments-agent/queue/pending/<file>.md \
   ~/.payments-agent/queue/approved/

# Or use sfos-ui (from solo-founder-os) for a unified dashboard across
# all SFOS agents:
sfos-ui
```

## Severity ladder

| Days overdue | Severity | Tone |
|---|---|---|
| 0–7 | gentle | "just a heads up" |
| 8–30 | firm | direct + mention next-step consequences |
| >30 | final | service suspension as next step |

## Status

v0.1 — mock provider only. Real Stripe wiring lands in v0.2 once the
agent has been validated against fixture data.

## License

MIT.
