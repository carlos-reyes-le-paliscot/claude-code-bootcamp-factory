---
name: human-gate
description: Decides whether a ticket being built needs a human before the factory continues, and if so asks in the right channel. Use during `build`, per ticket. Run it once before implementing a ticket, and again whenever the implementer hits a fork the ticket and plan don't settle, wants to deviate from plan.md, would have to bend an intent constraint or touch something irreversible or security-sensitive, or VERIFY keeps failing on the same cause. Defaults to autonomy. Most checks end in "proceed", some in "proceed and record the assumption", and few in "park the ticket and ask".
---

# Human gate

The factory runs on its own. This skill decides the rare moments when it shouldn't.

The gate measures each decision against the **intent** (`docs/intent/<NNN-slug>/intent.md`:
Problem, Proposed outcome, Affected users, Constraints, Open questions) and against what the
**plan** (`plan.md`: Decisions, Files that change, Risks, Out of scope) already settled. A human
approved the intent and the plan. Anything that stays inside them is already authorised. The gate
fires only where the work would leave that approved space, or where the documents don't say which
of two materially different paths to take.

Read `docs/agents/project.md` first (`HUMAN_GATE`, `VERIFY`, `UNTESTED`, Project rules) and
`docs/agents/issue-tracker.md` (labels, states, how to park a ticket).

## When to run it

| Moment | Who runs it |
| --- | --- |
| Before writing code for a ticket | The implementer, after fetching the ticket |
| On reaching a fork the ticket, plan and code don't settle | The implementer, before choosing |
| Before a change outside the plan's Decisions or Files that change | The implementer |
| VERIFY fails three times on the same root cause, or the only fix weakens a check | The implementer |
| An implementer returns a `HUMAN_GATE` block | The orchestrator (`build`), to route it |

Don't run it for mechanical work: renames, formatting, regenerated files, test scaffolding that
follows prior art.

## Step 1: gather what's already decided

Before you classify anything, collect:

1. The ticket with its comments (an earlier answer may be in a comment).
2. `intent.md`: the Proposed outcome and Constraints lines, which you will quote, and every
   Open question.
3. `plan.md`: Decisions (including "Resolved from intent"), Risks, Out of scope, and
   `## Decisions during build` if that section exists.

**Never ask a question these sources already answer.** If the plan resolved an open question, that
answer stands even if you'd have chosen differently. If the plan lists a risk ("flag for
reviewer"), the plan already accepted it, so it goes to the PR review list. It isn't a question.

## Step 2: classify the decision

Check the triggers in order. The first one that matches decides the outcome.

### PARK: stop the ticket and ask

Park only when **no path stays inside the intent and plan**, or when the paths differ in an outcome
a human owns. If a compliant path exists, take it and record it instead.

1. **Constraint pressure.** Every way forward breaks or reinterprets an intent Constraint. Examples:
   storing data the intent says not to keep, a new external service, a schema change the intent rules
   out, a migration that isn't reversible.
2. **Unresolved open question.** The ticket depends on an intent Open question that neither the
   plan nor `Decisions during build` answers, and the possible answers change behaviour users or
   the intent's metric would notice.
3. **Outcome fork.** Two or more readings of the ticket are reasonable, and they differ in user
   experience, a number the Proposed outcome measures, or who can see or do what. Code style and
   internal structure don't count.
4. **Plan contradiction.** The plan's Decision can't work as written (the code disproves it), or two
   tickets' acceptance criteria conflict.
5. **High-blast change outside the plan.** Any of these, when the plan doesn't already name it:
   - changes to auth, permissions or the superuser rule
   - token lifetime or contents, secrets
   - personal data that is stored, logged or sent
   - destructive operations on existing data
   - a new dependency
   - changes to shared fixtures or CI config that other tickets rely on
6. **Weakening the gate.** The only way to green is to skip or delete a test, loosen an
   assertion, add `# noqa`/`# pragma: no cover`/`eslint-disable`, lower coverage, or edit VERIFY
   config.
7. **Stuck.** VERIFY has failed three times on the same root cause and you no longer have a
   hypothesis worth testing.

### RECORD: proceed, and leave a trace for review

Proceed, and record the assumption (Step 4), when the decision is outside the plan's text, but:

- it is reversible and local to the ticket's files, **and**
- it stays inside every Constraint, **and**
- one option is clearly better for the Proposed outcome, or the options don't differ in anything a
  user or the metric would notice.

Typical cases:

- An extra error path the plan implies but doesn't spell out.
- A small helper in a file the plan didn't list.
- A test fixture adjustment confined to the ticket's tests.
- A diff that depends on an `UNTESTED` area.

### PROCEED: nothing to record

The ticket, the plan, or prior art in the code settles it. Carry on without logging anything.

When unsure between PARK and RECORD, ask: *if the human reads this in the PR, could they reasonably
have wanted the other path, and would undoing it cost more than a small follow-up commit?* Two
yeses mean PARK. Otherwise RECORD.

## Step 3: if PARK, write one decision request

One request per ticket at a time. Batch every open question for that ticket into it (at most
four). Use the format in [references/decision-request.md](references/decision-request.md). It must
be answerable without scrolling back:

- the question, in one sentence
- the intent or plan line that makes it a human call, quoted
- 2–4 options, each with its consequence, recommended option first
- what is blocked, and what keeps going without an answer

Then stop work on this ticket. Commit any work in progress to the ticket branch if it's worth
keeping, but **don't merge it into `intent/<NNN-slug>`**.

**Implementers (subagents, worktrees) never ask the human directly.** End your run by returning the
`HUMAN_GATE` block from the reference file to the orchestrator, and do nothing else on the ticket.

## Step 4: route the request (orchestrator)

`HUMAN_GATE` in `docs/agents/project.md` picks the channel. It defaults to `adaptive`:

- **`adaptive`**: if a person is driving this session interactively, ask inline with
  `AskUserQuestion`, using the decision request's options. If that tool isn't available, the call is
  refused, the session is headless (`claude -p`, CI, a scheduled run), or no answer comes back, fall
  through to `async`.
- **`inline`**: always ask in the session. If nobody can answer, behave as `async`.
- **`async`**: park the ticket in the issue tracker, as `issue-tracker.md` describes under
  "When a skill says park a ticket":
  1. Comment the decision request on the ticket.
  2. Remove `ready-for-agent` (this holds it back from `build`) and add `needs-human`.
  3. The ticket is back in the Todo role (see the state table in `issue-tracker.md`).

  Then **keep building**: pick the next unblocked ticket. Tickets blocked by the parked one wait
  through their "blocked by" dependencies, so no extra bookkeeping is needed.

  A human resumes the ticket by answering in a comment, removing `needs-human`, and re-adding
  `ready-for-agent`. The next `build` run reads that comment when it fetches the ticket.

If every remaining ticket is parked or blocked by a parked one, end the `build` run. List each
parked ticket with its question in one place: the run summary, plus the intent PR if one exists.

## Step 5: record the outcome

Every PARK answer and every RECORD assumption gets written down, so later tickets don't re-ask and
reviewers can audit what the factory decided on its own:

- **PARK, answered**: add a line under `## Decisions during build` in `plan.md` (create the section
  above `## Tickets` if it's missing), commit it on `intent/<NNN-slug>`, then resume the ticket:
  `- GH-<n> (<date>, <who answered>): <question> → <answer>`
- **RECORD**: add an "Assumptions" bullet in the ticket's final commit message body, and in the
  intent PR's review list when that PR is opened or updated:
  `- GH-<n>: assumed <X> because <intent/plan reason>; reversible by <how>.`

## Calibration

[references/calibration.md](references/calibration.md) has worked cases from intents 001 and 002
showing where the line falls. Read it the first time you use this skill in a session.
