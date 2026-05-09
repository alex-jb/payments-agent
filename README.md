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

---

## 🧩 Part of the [Solo Founder OS](https://github.com/alex-jb/solo-founder-os) stack

A growing collection of MIT-licensed agents that share `solo-founder-os` as their base — cron, eval, reflexion, AnthropicClient, HITL queue, notifiers. Each agent is independently useful; together they cover the full one-person company workflow.

🌐 The whole stack is live in production at [vibexforge.com](https://vibexforge.com).

| Agent | What it does |
|---|---|
| [solo-founder-os](https://github.com/alex-jb/solo-founder-os) | The shared base lib (cron · eval · reflexion · skill library · DGM-lite). Every other agent depends on it. |
| [build-quality-agent](https://github.com/alex-jb/build-quality-agent) | Pre-push Claude diff reviewer + local build runner — catches CI-killing changes before they ship. |
| [customer-discovery-agent](https://github.com/alex-jb/customer-discovery-agent) | Reddit pain-point scraper + Claude clustering for product validation. |
| [funnel-analytics-agent](https://github.com/alex-jb/funnel-analytics-agent) | Daily founder brief + real-time PH-day alerts across 9 sources. |
| [orallexa-marketing-agent](https://github.com/alex-jb/orallexa-marketing-agent) | AI marketing agent — submit project once, get platform-native posts for X / Reddit / HN / Dev.to / 小红书 + 7 more. Powers [vibexforge.com](https://vibexforge.com). |
| [vc-outreach-agent](https://github.com/alex-jb/vc-outreach-agent) | Cold email drafter — investors (vc mode) or paying customers (customer mode, merged from customer-outreach in v0.9.0). HITL queue + SMTP sender. |
| [cost-audit-agent](https://github.com/alex-jb/cost-audit-agent) | Monthly bill audit across 6 providers (Vercel / Anthropic / OpenPanel / HyperDX / Supabase / GitHub Actions) with dollar-tagged waste findings. |
| [bilingual-content-sync-agent](https://github.com/alex-jb/bilingual-content-sync-agent) | EN ⇄ 中文 i18n diff + Claude translate + HITL apply. Batch API path @ 50% off. |
| [customer-support-agent](https://github.com/alex-jb/customer-support-agent) | Triage user messages → auto-draft replies → HITL queue. Closes the L5 customer-support layer. |

*Each agent's own row is omitted from its README. Install whichever solve real problems for you — `pip install <agent-name>`.*
