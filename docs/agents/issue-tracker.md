# Issue tracker: GitHub Issues

<!-- Copied to docs/agents/issue-tracker.md by /feature-factory:setup.
     The conventions below are what to-tickets and build assume. -->

Work is tracked in GitHub Issues on `ISSUE_REPO` (from `docs/agents/project.md`), through the
GitHub MCP server or the `gh` CLI. Use the MCP server when it is connected and `gh` otherwise.
Blocking relations go through `gh api`, because the MCP server has no tool for them.

## Conventions

- Each intent gets one GitHub milestone, named `<NNN-slug>` after its `docs/intent/` directory.
  Every ticket for the intent goes in that milestone.
- Ticket identifiers are `GH-<n>`, where `<n>` is the issue number. GitHub autolinks `GH-<n>` to
  the issue. A bare `#<n>` can't start a commit message, because git treats the line as a comment.
- Branches are `feat/gh-<n>-<slug>`. Commits start with `GH-<n>:`. The intent PR closes its
  tickets with `Closes #<n>` lines, one per ticket. These take effect when the PR merges into the
  default branch.
- Every ticket carries the `ready-for-agent` label. Remove it to hold a ticket back from `build`.
  Add `REPO_LABEL` as well when it isn't `—`.
- Blocking is a real GitHub issue dependency ("blocked by"), never prose. `build` reads the
  dependencies to find what is unblocked:

  ```sh
  # GH-12 is blocked by GH-11. issue_id is the blocker's numeric id, not its number.
  BLOCKER_ID=$(gh api repos/$ISSUE_REPO/issues/11 --jq .id)
  gh api -X POST repos/$ISSUE_REPO/issues/12/dependencies/blocked_by -F issue_id=$BLOCKER_ID

  # What blocks GH-12? It is unblocked when every result is closed.
  gh api repos/$ISSUE_REPO/issues/12/dependencies/blocked_by --jq '.[] | "\(.number) \(.state)"'
  ```

## Labels

Create these once per repo. Adding a label that doesn't exist yet to an issue also creates it.

| Label | Meaning |
| --- | --- |
| `ready-for-agent` | `build` may pick the ticket up. |
| `status:in-progress` | An implementer has the ticket. |
| `status:in-review` | The ticket is on the intent's PR. |
| `needs-human` | Parked by `human-gate`. The question is the latest comment. Never set together with `ready-for-agent`. |

## Ticket states

When a skill names a role, use the GitHub state mapped to it here. A ticket has at most one
`status:` label at a time.

| Role | GitHub | Meaning |
| --- | --- | --- |
| Todo | Open, no `status:` label | Published by `to-tickets`, not started. |
| In Progress | Open, `status:in-progress` | An implementer has it. |
| In Review | Open, `status:in-review` | On the intent's PR. Link the PR in a comment on the ticket. |
| Done | Closed as completed | The PR is merged. Its `Closes #<n>` lines close the ticket. |

## When a skill says "publish to the issue tracker"

Create the issue in `ISSUE_REPO`, using the `to-tickets` template, in the intent's milestone, with
the labels above. Then add its "blocked by" dependencies.

## When a skill says "fetch the relevant ticket"

Read the issue with its comments, its labels, and its `blocked_by` dependencies.

## When a skill says "park a ticket"

Used by `human-gate` when a decision needs a human and nobody is answering inline.

1. Comment the decision request on the issue (format: `.claude/skills/human-gate/references/decision-request.md`).
2. Remove `ready-for-agent` and any `status:` label, then add `needs-human`. The ticket is back in Todo.

To resume, a human answers in a comment, removes `needs-human` and re-adds `ready-for-agent`.
