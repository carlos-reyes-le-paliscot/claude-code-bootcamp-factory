#!/usr/bin/env python3
"""System 1 pass for the human gate: a fast first look at one build decision.

TypeSafe's Jev is a "System One" decision model. It doesn't generate text. One POST
sends a `state` plus typed yes/no (`noul`) questions, and gets back a 0-1 probability
for each question. This script asks Jev the human gate's questions about one
decision, then routes it:

- `proceed`    Jev is confident the decision is already settled and trips no trigger.
- `record`     Jev is confident it is reversible and local, and trips no trigger.
- `deliberate` Anything else. System 2 takes over: the full rules in SKILL.md Step 2,
               applied by the agent, which can still end in PROCEED, RECORD or PARK.

Jev never parks a ticket and never talks to a human. It only lets clear cases skip
deliberation. Every failure (no key, timeout, non-200, a malformed answer) routes to
`deliberate`. That is the safe fallback, because a wrong `proceed` costs more than a
wrong escalation.

Usage:
    python3 system1.py decision.json        # one decision; prints JSON
    python3 system1.py --eval [cases.json]  # threshold check against calibration cases

Environment: JEV_API_KEY (unset means always `deliberate`), plus optional JEV_MODEL
and JEV_API_URL. The wire format follows the TypeSafe API reference (POST
/v1/systemone, Bearer auth).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = os.environ.get("JEV_API_URL") or "https://api.typesafe.ai/v1/systemone"
MODEL = os.environ.get("JEV_MODEL") or "jev-latest"
TIMEOUT_S = 3.0

# A trigger at or above this sends the decision to System 2. The bar is
# deliberately low: Jev's scores for borderline text sit near 0.5, and a missed
# trigger is the expensive mistake.
ESCALATE_AT = 0.30
# A fast path needs every trigger below this...
QUIET_BELOW = 0.15
# ...and the fast path's own question at or above this.
CONFIDENT_AT = 0.80

TRIGGERS: dict[str, str] = {
    "breaks_constraint": (
        "Would every way forward break or reinterpret one of the intent's Constraints?"
    ),
    "open_question": (
        "Does the decision depend on one of the intent's Open questions that neither "
        "the plan nor 'Decisions during build' answers?"
    ),
    "outcome_fork": (
        "Are there two or more reasonable choices here that differ in what users see, "
        "in a number the intent's Proposed outcome measures, or in who can see or do "
        "what? Code style and internal structure don't count."
    ),
    "plan_contradiction": (
        "Does the decision show that a plan Decision can't work as written, or that "
        "two tickets' acceptance criteria conflict?"
    ),
    "high_blast": (
        "Does the decision touch any of these without the plan naming it: auth, "
        "permissions or the superuser rule; token lifetime or contents; secrets; "
        "storing, logging or sending personal data; destructive operations on "
        "existing data; a new dependency; or shared test fixtures or CI config?"
    ),
}

QUESTIONS: dict[str, dict[str, str]] = {
    "settled": {
        "type": "noul",
        "instructions": (
            "Do the ticket, the plan's Decisions, Risks or Out of scope, or "
            "'Decisions during build' already settle this decision, so that no new "
            "choice is being made?"
        ),
    },
    "reversible_local": {
        "type": "noul",
        "instructions": (
            "Is the choice easy to reverse with a small follow-up commit, and "
            "confined to this ticket's own files and tests?"
        ),
    },
    **{k: {"type": "noul", "instructions": v} for k, v in TRIGGERS.items()},
}


def precheck(decision: dict[str, Any]) -> str | None:
    """Deterministic triggers. Jev is never asked to wave these through."""
    signals = decision.get("signals") or {}
    if int(signals.get("verify_failures", 0)) >= 3:
        return "stuck: VERIFY failed three times on the same cause"
    if signals.get("weakens_gate"):
        return "weakening the gate: the diff skips a test, loosens a check or lowers coverage"
    return None


def build_state(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "context": (
            "An autonomous software factory is building one ticket of an approved "
            "intent and plan. A human approved the intent and the plan, so anything "
            "inside them is authorised. Judge the decision below against them."
        ),
        "ticket": decision.get("ticket", ""),
        "decision": decision.get("decision", ""),
        "intent": decision.get("intent", ""),
        "plan": decision.get("plan", ""),
    }


def ask_jev(state: dict[str, Any], key: str) -> dict[str, Any]:
    body = json.dumps({"model": MODEL, "state": state, "questions": QUESTIONS}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as res:
        return json.loads(res.read())


def probabilities(answers: dict[str, Any]) -> dict[str, float]:
    """Pull each `noul` probability out of the response. Raises if any is missing."""
    out: dict[str, float] = {}
    for k in QUESTIONS:
        a = answers.get(k)
        p = a.get("noul") if isinstance(a, dict) and a.get("type") == "noul" else None
        if not isinstance(p, int | float) or isinstance(p, bool):
            raise TypeError(f"malformed answer for {k!r}: {a!r}")
        out[k] = float(p)
    return out


def route(p: dict[str, float]) -> tuple[str, list[str]]:
    """Asymmetric routing: escalate on any hint of a trigger, and fast-path only on clear cases."""
    hot = [k for k in TRIGGERS if p[k] >= ESCALATE_AT]
    if hot:
        return "deliberate", [f"{k}={p[k]:.2f}" for k in hot]
    quiet = all(p[k] < QUIET_BELOW for k in TRIGGERS)
    if quiet and p["settled"] >= CONFIDENT_AT:
        return "proceed", [f"settled={p['settled']:.2f}"]
    if quiet and p["reversible_local"] >= CONFIDENT_AT:
        return "record", [f"reversible_local={p['reversible_local']:.2f}"]
    return "deliberate", ["no confident fast path"]


def classify(decision: dict[str, Any]) -> dict[str, Any]:
    local = precheck(decision)
    if local:
        return {"route": "deliberate", "source": "local", "reasons": [local]}

    key = os.environ.get("JEV_API_KEY")
    if not key:
        return {
            "route": "deliberate",
            "source": "unavailable",
            "reasons": ["JEV_API_KEY unset"],
        }

    state = build_state(decision)
    # Mirrors the wire body minus auth, so prompts can be tuned against real answers.
    request = {"model": MODEL, "state": state, "questions": QUESTIONS}
    started = time.monotonic()
    try:
        res = ask_jev(state, key)
        p = probabilities(res.get("answers") or {})
    except (urllib.error.URLError, TimeoutError, ValueError, TypeError) as err:
        return {
            "route": "deliberate",
            "source": "unavailable",
            "reasons": [f"jev failed: {err}"],
            "ms": round((time.monotonic() - started) * 1000),
            "request": request,
        }
    verdict, reasons = route(p)
    return {
        "route": verdict,
        "source": "jev",
        "model": res.get("model", MODEL),
        "reasons": reasons,
        "probabilities": {k: round(v, 3) for k, v in p.items()},
        "ms": round((time.monotonic() - started) * 1000),
    }


def run_eval(path: Path) -> int:
    """Routes every calibration case, then reports misses and the fast-path rate.

    A PARK case routed to `proceed` or `record` is a critical miss and fails the
    run. Check the thresholds against this before trusting them on a new workload.
    """
    cases = json.loads(path.read_text())
    critical, fast, rows = 0, 0, []
    for case in cases:
        got = classify(case)
        want = case["expected"]  # PROCEED | RECORD | PARK, from calibration.md
        ok = {
            "PROCEED": got["route"] in ("proceed", "deliberate"),
            "RECORD": got["route"] in ("record", "deliberate"),
            "PARK": got["route"] == "deliberate",
        }[want]
        critical += want == "PARK" and not ok
        fast += got["route"] != "deliberate"
        rows.append(
            f"{'ok ' if ok else 'MISS'} {case['id']:<8} {want:<8} -> {got['route']:<10} {', '.join(got['reasons'])}"
        )
    print("\n".join(rows))
    print(f"\n{len(cases)} cases, {fast} took a fast path, {critical} critical misses")
    return 1 if critical else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--eval"]:
        default = (
            Path(__file__).resolve().parent.parent
            / "references"
            / "calibration-cases.json"
        )
        return run_eval(Path(argv[1]) if len(argv) > 1 else default)
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps(classify(json.loads(Path(argv[0]).read_text())), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
