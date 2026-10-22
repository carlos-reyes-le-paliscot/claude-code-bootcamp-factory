# Calibration: where the line falls

These cases come from this repo's intents: 001-new-user-onboarding (FAS-1..8) and
002-remember-me-login (FAS-9..11). Each case gives the situation, the outcome, and the reason. The FAS ids are the original Linear
ticket ids. New tickets are `GH-<n>` issues.

## PROCEED: already decided

**FAS-2. A user changes their name from empty to "Alice".** Does that count as a name edit?
→ PROCEED. The plan's Decisions settle it: "`mark_name_edited` when `full_name` changes to a
different non-empty value". The intent listed this as an open question. The plan resolved it, so
the question is closed.

**FAS-1. Existing users get no onboarding row.** Should you backfill them?
→ PROCEED (no backfill). The plan says "Rows created only in `POST /users/signup`. Existing users …
no row", and it lists backfill as out of scope.

**FAS-2. The hook in `POST /items/` touches an item route, and the intent's constraint says "no
changes to item features".**
→ PROCEED. The plan's Risks already name it ("keep to one call, no behaviour change; flag for
reviewer"). It goes on the PR review list. It isn't a question.

**Any ticket. VERIFY reports ruff DTZ011 in `scripts/` or `hooks/`.**
→ PROCEED, and don't fix it. `UNTESTED` in `project.md` lists those five violations as pre-existing.

## RECORD: proceed, leave a trace

**FAS-4. SMTP answers with something other than 250.** The plan says "`invite_sent_at` set only
after a successful send" but doesn't define success.
→ RECORD. Treat a non-250 reply as a failed send, return 502, and leave the step and the count
untouched. This is the only reading consistent with the plan. It is reversible and stays inside the
constraints. (The factory did exactly this in review round 1.)

**FAS-4. The cap check and the increment race under concurrent requests.**
→ RECORD. Lock the row from the check through the increment. The plan decided on the cap. Enforcing
it correctly is implementation, not a new decision.

**FAS-10. The `sessionStorage` token is per tab, so opening a second tab means logging in again.**
→ RECORD, as a PR review-list note. The plan's Risks already accept it.

## PARK: a human owns this

**FAS-4. To enforce the 5-send cap per recipient, you'd need to remember who was invited.**
→ PARK (constraint pressure). The intent says "Do not store invited email addresses longer than
needed to send the email", and the plan's cap counts per user, not per address. Proceeding with the
plan's per-user cap is the compliant path, so take it. Park only if the ticket's acceptance criteria
insist on per-recipient limits.

**FAS-9. The cleanest test hook is to put a `remember` claim in the JWT.**
→ Don't do it, and don't ask. The constraint says "the same JWT access token … no new claims", and a
compliant path exists (decode `exp` in the test). Switch paths. If no compliant path existed, this
would be a PARK for constraint pressure.

**FAS-10. Ticking "Remember me" in `auth.setup.ts` still leaves some e2e specs logged out, and
making the checkbox default to checked would fix them.**
→ PARK (outcome fork, and it would weaken the intent). The intent says "Remember me checkbox, off
by default", and the default exists to protect shared-machine users. Changing it to fix tests
changes the product. Ask, and offer options such as fixing the specs' storage state versus a
test-only default.

**FAS-5. The stats query only passes the 90% coverage gate if an error branch gets
`# pragma: no cover`.**
→ PARK (weakening the gate). A test for the branch is the compliant path. Park only if the branch
is truly unreachable from a test, and say why.

**FAS-1. The migration's downgrade would also need to alter the `user` table.**
→ PARK (high-blast outside the plan). The intent says "No change to the user table beyond what the
feature needs", and the plan says "`user` table untouched".

**FAS-11. Remembered sessions turn out to need a refresh token to meet "stays logged in".**
→ PARK (plan contradiction, constraint pressure). Refresh tokens are out of scope, and the
constraint says "No change to how tokens work". The 30-day expiry is the plan's answer. If the code
shows it can't work, a human decides.

## The test, restated

PARK means the human could reasonably have wanted the other path, **and** undoing your choice would
cost more than a small follow-up. If either half is false, the outcome is RECORD or PROCEED.
