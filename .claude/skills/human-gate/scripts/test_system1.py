"""Unit tests for system1.py. Run: python3 -m unittest discover .claude/skills/human-gate/scripts"""

import os
import unittest
import urllib.error
from unittest import mock

import system1

QUIET = {k: 0.05 for k in system1.TRIGGERS}


def probs(**over: float) -> dict[str, float]:
    return {"settled": 0.1, "reversible_local": 0.1, **QUIET, **over}


def answers(p: dict[str, float]) -> dict:
    return {
        "model": "jev-test",
        "answers": {k: {"type": "noul", "noul": v} for k, v in p.items()},
    }


class Route(unittest.TestCase):
    def test_settled_and_quiet_proceeds(self) -> None:
        self.assertEqual(system1.route(probs(settled=0.9))[0], "proceed")

    def test_reversible_and_quiet_records(self) -> None:
        self.assertEqual(system1.route(probs(reversible_local=0.9))[0], "record")

    def test_any_trigger_escalates_even_when_settled(self) -> None:
        verdict, reasons = system1.route(probs(settled=0.95, high_blast=0.35))
        self.assertEqual(verdict, "deliberate")
        self.assertEqual(reasons, ["high_blast=0.35"])

    def test_lukewarm_trigger_blocks_the_fast_path(self) -> None:
        # Below the escalation bar, but not quiet enough to skip System 2.
        self.assertEqual(
            system1.route(probs(settled=0.95, outcome_fork=0.2))[0], "deliberate"
        )

    def test_unconfident_goes_to_system_two(self) -> None:
        self.assertEqual(system1.route(probs(settled=0.7))[0], "deliberate")


DECISION = {"ticket": "GH-1", "decision": "x", "intent": "", "plan": ""}


class Classify(unittest.TestCase):
    def test_stuck_never_calls_jev(self) -> None:
        with mock.patch.object(system1, "ask_jev") as ask:
            got = system1.classify({**DECISION, "signals": {"verify_failures": 3}})
        ask.assert_not_called()
        self.assertEqual((got["route"], got["source"]), ("deliberate", "local"))

    def test_weakening_gate_never_calls_jev(self) -> None:
        with mock.patch.object(system1, "ask_jev") as ask:
            got = system1.classify({**DECISION, "signals": {"weakens_gate": True}})
        ask.assert_not_called()
        self.assertEqual(got["route"], "deliberate")

    def test_no_key_falls_back_to_system_two(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            got = system1.classify(DECISION)
        self.assertEqual((got["route"], got["source"]), ("deliberate", "unavailable"))

    @mock.patch.dict(os.environ, {"JEV_API_KEY": "k"})
    def test_jev_error_falls_back_to_system_two(self) -> None:
        with mock.patch.object(
            system1, "ask_jev", side_effect=urllib.error.URLError("down")
        ):
            got = system1.classify(DECISION)
        self.assertEqual(got["route"], "deliberate")
        self.assertEqual(
            set(got["request"]), {"model", "state", "questions"}
        )  # no auth echoed

    @mock.patch.dict(os.environ, {"JEV_API_KEY": "k"})
    def test_malformed_answer_falls_back_to_system_two(self) -> None:
        bad = answers(probs(settled=0.9))
        bad["answers"]["high_blast"] = {"type": "choice", "choice": "x"}
        with mock.patch.object(system1, "ask_jev", return_value=bad):
            self.assertEqual(system1.classify(DECISION)["route"], "deliberate")

    @mock.patch.dict(os.environ, {"JEV_API_KEY": "k"})
    def test_confident_answer_takes_the_fast_path(self) -> None:
        with mock.patch.object(
            system1, "ask_jev", return_value=answers(probs(settled=0.92))
        ):
            got = system1.classify(DECISION)
        self.assertEqual((got["route"], got["source"]), ("proceed", "jev"))
        self.assertEqual(got["probabilities"]["settled"], 0.92)


if __name__ == "__main__":
    unittest.main()
