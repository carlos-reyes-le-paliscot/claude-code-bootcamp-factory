# Issue tracker: Linear

<!-- Copied to docs/agents/issue-tracker.md by /feature-factory:setup.
     The conventions below are what to-tickets and build assume. -->

Work is tracked in Linear, through the Linear MCP server. Team and labels come from
`docs/agents/project.md`.

## Conventions

- One Linear project per intent, named `<NNN-slug>` after its `docs/intent/` directory.
- Ticket identifiers are `<LINEAR_TEAM>-<n>`. Branches are `feat/<team>-<n>-<slug>`, commits start
  with `<LINEAR_TEAM>-<n>:`, and PRs close tickets with `Closes <LINEAR_TEAM>-<n>` lines.
- Every ticket carries `ready-for-agent` and `REPO_LABEL`. Remove `ready-for-agent` to hold a
  ticket back from `build`.
- `needs-human` marks a ticket the `human-gate` skill parked: its question is the latest comment.
  It never carries `ready-for-agent` at the same time.
- Blocking is a real Linear "blocked by" relation, never prose. `build` reads the relations to
  find what is unblocked.

## Ticket states

When a skill names a role, use the Linear state mapped to it here.

| Role | Linear state | Meaning |
| --- | --- | --- |
| Todo | Todo | Published by `to-tickets`, not started. |
| In Progress | In Progress | An implementer has it. |
| In Review | In Review | On the intent's PR, which is commented on the ticket. |
| Done | Done | The PR is merged. Its `Closes` lines do this through Linear's GitHub integration. |

## When a skill says "publish to the issue tracker"

Create the issue in team `LINEAR_TEAM`, in the intent's project, with the `to-tickets` template.

## When a skill says "fetch the relevant ticket"

Read the issue with its comments and its blocking relations.

## When a skill says "park a ticket"

Used by `human-gate` when a decision needs a human and nobody is answering inline.

1. Comment the decision request on the ticket (format: `.claude/skills/human-gate/references/decision-request.md`).
2. Remove `ready-for-agent`, add `needs-human`.
3. Set the state to Todo.

To resume, a human answers in a comment, removes `needs-human` and re-adds `ready-for-agent`.
