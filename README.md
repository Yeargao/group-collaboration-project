# Group Collaboration Software — educational starter implementation

This is a **partial implementation / starter project**, not a verified full submission of the v0.1 specification. The authoritative eight specification files are in `specs/`. Python 3.10+ and Git are required; a GitHub remote named `origin` is required for publishing.

## Quick start (PowerShell)

```powershell
python -m groupctl --help
python -m groupctl init --group G-12
python -m groupctl member P17 Alice
python -m groupctl identity P17
# commit/push the .group metadata and configure GitHub origin
# create a personal branch: git switch -c people/P17/parser
python -m groupctl status
python -m groupctl sync
```

For a finished coherent change, inspect and commit it first, then:

```powershell
python -m groupctl pub --summary "Implement parser" --test "python -m unittest discover -s tests"
python -m groupctl inspect C-xxxxxxxx
python -m groupctl integrate C-xxxxxxxx
```

To publish an event, create a JSON payload with the event-type-specific fields from `specs/03_event_format_contract.md`, then:

```powershell
python -m groupctl record review review_payload.json --push
```

## Important limitations

- `groupctl` provides mechanical primitives; the AI agent must do actual code review, test execution, conflict resolution, and semantic verification.
- `sync` merges canonical into a clean current branch, but event discovery does not yet track which events were already processed.
- `pub` requires a previously committed clean worktree and does not itself run tests or scan secrets. The agent must perform those steps.
- `integrate` merges but does not automatically run tests, create integration records, or push the integrated branch.
- `record` does not yet validate all event-type-specific required fields.
- `FINAL` is documented in `AGENTS.md` but not yet automated by the CLI.
- Concurrent event publication on separate branches may require an explicit event-sharing convention to ensure discoverability.

Do not claim the teacher's 15-step demonstration is complete until it has been exercised with three clones and GitHub, including a real conflict and finalization.
