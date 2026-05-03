# Contributing

Thanks for considering a contribution. This is agent #11 in the
[Solo Founder OS](https://github.com/alex-jb/solo-founder-os) stack —
each agent is small, single-purpose, and shares the common base library.

## Quick start

```bash
git clone https://github.com/alex-jb/payments-agent.git
cd payments-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the test suite
pytest -q

# Run the linter
ruff check .

# Smoke-test (uses MockProvider — no Stripe key needed)
python -m payments_agent triage
```

If anything in those five commands fails on a fresh clone, that's a bug.
Open an issue.

## What's a good first PR

- **Real Stripe wiring** in `stripe_provider.StripeProvider.fetch_overdue_invoices`
  — the v0.1 stub is documented; the path is `stripe.Invoice.list(status="open", ...)`
  and a `_to_invoice(raw)` helper.
- **Localized templates** — the template fallback is English-only. A
  zh-CN / es / ja variant set keyed off `Customer.metadata['locale']`.
- **Better severity bands** — current ladder is 7 / 30 day cutoffs. If
  a customer has paid late before but always pays, "firm" might be too
  harsh. A `gentle_hold_days` per-customer override would be cleaner.
- **Test isolation** — every new test should use the existing
  `conftest.py`'s `SFOS_TEST_MODE=1` env guard. PRs that bypass it
  by writing to real `~/.payments-agent/` will be asked to refactor.

## What's a hard sell

- **Auto-send approved drafts.** This is deliberately HITL-only in v0.1.
  Money-sensitive emails should go through human eyes. If you want
  auto-send for low-severity / low-amount cases, please open an issue
  to discuss the policy before writing the code.
- **Dropping the system-prompt safety rules** (NEVER thank for unpaid /
  EXACT amount / NEVER invent payment links). These are asserted in
  tests for a reason.

## Code style

- `ruff` for both linting and formatting
- Type-hint public functions; tests can be loose
- Docstrings for any module-level function
- ≤100 chars per line preferred; not enforced

## Tests

We aim for one happy-path test + one error-path test per non-trivial
function. Mock the `AnthropicClient` for any test that would otherwise
hit the API. Never write to `~/.payments-agent/` from a test — the
`SFOS_TEST_MODE=1` guard in `conftest.py` is your friend.

## License

MIT. Contributions are accepted under the same license.
