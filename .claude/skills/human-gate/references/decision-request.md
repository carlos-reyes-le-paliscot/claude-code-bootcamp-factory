# Decision request format

## Implementer → orchestrator: the `HUMAN_GATE` block

An implementer that parks a ticket ends its run with exactly this block, and nothing after it:

```
HUMAN_GATE
ticket: GH-<n>
trigger: <constraint-pressure | open-question | outcome-fork | plan-contradiction | high-blast | weakening-gate | stuck>
branch: feat/gh-<n>-<slug>   (WIP commit: <sha> | none)
system1: <route and the reasons system1.py returned, e.g. "deliberate: high_blast=0.71" | off | unavailable>
questions:
  - question: <one sentence, ends with ?>
    why_human: "<quoted intent/plan line>" (intent.md § Constraints)
    options:
      - label: <1–5 words> (Recommended)
        consequence: <what happens, what it costs>
      - label: <…>
        consequence: <…>
blocked: <what can't proceed: this ticket, and GH-x/GH-y through blocking relations>
continues: <what the factory can still do without the answer>
```

## Orchestrator → human, inline (`AskUserQuestion`)

Map each `questions` entry to one question:

- `header`: the ticket id, e.g. `GH-10`
- `question`: the question, followed by the quoted why-line
- `options`: the labels and consequences, keeping "(Recommended)" on the first

The human can always pick "Other" to give a free-text answer.

## Orchestrator → issue tracker (async): the ticket comment

```markdown
**Needs a human decision. This ticket is parked (`needs-human`).**

**Question:** <question>

**Why this isn't the factory's call:** <intent or plan line, quoted> (<file § section>)

**Options**
1. **<label> (recommended)**: <consequence>
2. **<label>**: <consequence>

**Blocked:** <…>
**Still moving:** <…>

To resume: reply with the option (or your own answer), remove `needs-human`, and add
`ready-for-agent`. The answer will be recorded under "Decisions during build" in `plan.md`.
```

## Quality bar

- The question is a real fork. Don't ask for permission to do what the plan already says.
- The recommended option is the one you'd ship if forced. Say why in its consequence.
- Consequences name concrete effects, like "unchecked users must log in again in a second tab". A
  bare "more complex" doesn't count.
- Never paste secrets, tokens, or personal data (for example an invitee's email address) into a
  comment.
