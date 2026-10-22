# Project config

<!-- Copy to docs/agents/project.md in the repo and fill every row.
     Write `—` for a key that does not apply. The feature-factory
     skills and agents read this file first. -->

| Key | Value | Notes |
| --- | --- | --- |
| `ISSUE_REPO` | `carlos-reyes-le-paliscot/claude-code-bootcamp-factory` | GitHub repo whose Issues hold the tickets. Tickets are `GH-<n>`, branches `feat/gh-<n>-<slug>`. |
| `REPO_LABEL` | `—` | Label for this repo's tickets. Needed only when `ISSUE_REPO` holds tickets for several code repos. |
| `INTENT_HOME` | `this repo` | Where `docs/intent/` lives: `this repo`, or `owner/repo` for a shared home. |
| `SETUP` | `uv sync --all-packages && bun install --frozen-lockfile` | Installs dependencies in a fresh worktree. Idempotent; must not write `.git/config` or `.git/hooks`. |
| `VERIFY` | `uv run prek run --from-ref origin/master --to-ref HEAD` | The gate. Passes only on exit 0. |
| `HUMAN_GATE` | `adaptive` | How `human-gate` asks: `adaptive` (inline when someone is driving the session, else park in the tracker), `inline`, or `async`. |
| `UNTESTED` | Backend pytest and the 90% coverage gate (need Postgres and mailpit via Docker); Playwright e2e; 5 existing ruff DTZ011 violations in `scripts/` and `hooks/` that a changed-files gate doesn't see | Optional. What `VERIFY` can't reach (e2e, live third-party calls). Lands in the PR's review list when the diff depends on it. |

## Project rules

<!-- Repo-specific rules for implementers and the review. -->
