# Human-to-agent collaboration instructions (protocol 0.1)
Read all files in `specs/` before executing collaboration commands. The files are authoritative. Commands below are **human prompts to the agent**, not necessarily direct CLI commands.

- SYNC: protect uncommitted work; inspect branch/commit; fetch; read new events; update canonical safely; check affected assumptions and quick tests. `python -m groupctl sync` assists but does not replace judgment.
- PUB: inspect diff for secrets/junk; run relevant tests; commit coherent changes on personal branch; `python -m groupctl pub --summary "..." --test "..."`; report change ID. Do not merge into main.
- INT C-17: `python -m groupctl inspect C-17`; inspect actual diff; integrate only after understanding interfaces; use `python -m groupctl integrate C-17` if appropriate; resolve conflicts by reasoning, never arbitrarily; run build/tests/semantic checks; publish `integration_result` event.
- REV C-17: inspect published event, actual diff, surrounding code and tests; choose one verdict from spec; publish `review` event; do not merge.
- TEST [scope]: identify exact commit; run applicable tests/build/static/UI checks; investigate failures; document manual checks; publish `test_result` event. Do not change expected outputs just to pass.
- STATUS: inspect local and remote Git state, pending events, tests and blockers; `python -m groupctl status` is a starting point.
- FINAL: synchronize, assess pending changes, blockers and test evidence; verify canonical commit; run final tests; prepare `.group/final/candidate.md` and show human; only after explicit confirmation publish `final_report.md`, `final.json` and `final_result` event. Never submit a private branch.

Use `python -m groupctl record TYPE payload.json --push` for structured events. Follow exact JSON fields and values in `specs/03_event_format_contract.md`. Do not share private chat logs. Do not force-push canonical branches or discard another person's work. If a command's required step is not automated by `groupctl`, carry it out explicitly with Git, testing tools and your own reasoning; never pretend it happened.
