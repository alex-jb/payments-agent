# Security policy

## Supported versions

Only the latest minor (currently `0.1.x`) gets security fixes. v0.x is
pre-1.0; the API may change.

## Reporting a vulnerability

Email **alex@vibexforge.com** with subject prefix `[security] payments-agent`.
Do NOT open a public GitHub issue for security findings. Initial response
within 72 hours.

## In-scope concerns we care about most

This agent handles money-adjacent state. Specifically:

1. **Prompt-injection in customer-controlled fields.** `Customer.name` and
   `Invoice.description` flow into the Claude prompt. A malicious customer
   setting their Stripe display name to an instruction-shaped string
   could try to override the system prompt. The system prompt's hard
   rules (NEVER thank for unpaid / EXACT amount / NEVER invent payment
   link) are first defense; report if you find a way around them.
2. **Hallucinated payment links.** Even though the system prompt forbids
   it, structured output beta has rare hiccups. If you can produce a
   draft that contains a URL not present in the input invoice, that's
   a security bug.
3. **Wrong-amount drafts.** Anything that produces a draft whose body
   mentions a different amount than the invoice (off-by-one cents,
   currency mismatch, rounded values) is a security bug.
4. **Stripe credential exfiltration.** This agent is designed to never
   write `STRIPE_API_KEY` to any log or queue file. If you find a path
   that does, that's high-severity.

## Out of scope

- The mock provider's fixture data is intentionally fake. Issues about
  test fixtures don't qualify.
- Bug reports about the v0.1 real Stripe stub raising `NotImplementedError` —
  that's the documented v0.1 behavior; real wiring lands in v0.2.
- Side-channel timing attacks against a local CLI are not relevant to
  the threat model.

## Defense-in-depth choices already made

- **HITL-only in v0.1.** No auto-send. Every draft requires human
  approval to actually leave the queue.
- **System prompt + tests pin the safety rules.** A future prompt
  rewrite that removes them will fail
  `test_drafter.test_system_prompt_*`.
- **`SFOS_TEST_MODE=1` in tests** — prevents test fixtures polluting
  the real reflexion store with money-shaped strings.
