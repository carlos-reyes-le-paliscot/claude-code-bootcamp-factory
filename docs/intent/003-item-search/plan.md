# Plan: Search items (from intent.md 2026-10-22)

## Solution

`GET /items/` accepts an optional `q`. When present, the list and its `count` are narrowed to items that match, under the same ownership rule as today. The items page gets a search input above the table that refetches with `q`.

## Decisions

- Backend: `read_items` gains `q: str | None = None` (max length 100). When `q` is non-empty after trimming, both the count and list statements add a filter; ownership filtering is unchanged. No `q` or an empty `q` takes today's code path.
- Matching ignores case (`ILIKE '%q%'`, with `%` and `_` in `q` escaped).
- Frontend: a search `Input` from `components/ui` above the items table, debounced 300 ms, with `data-testid="items-search"`. The query key becomes `["items", { q }]`. An empty result with a search term shows "No items match" instead of the empty-state copy.
- Client regenerated with `scripts/generate-client.sh`.
- Resolved from intent: matching ignores case.

## Files that change

- Modified: `backend/app/api/routes/items.py`, `backend/tests/api/routes/test_items.py`
- Modified: `frontend/src/routes/_layout/items.tsx`, `frontend/tests/items.spec.ts`
- Generated: `frontend/src/client/*`, `frontend/openapi.json`

## Order of work

1. Backend `q` filter with tests.
2. Regenerate the client.
3. Search input on the items page; Playwright test.

## Testing seams

- Backend: `GET /items/?q=` through the `client` fixture with `normal_user_token_headers` and `superuser_token_headers`. Prior art: `backend/tests/api/routes/test_items.py`.
- Frontend: Playwright on the items page. Prior art: `frontend/tests/items.spec.ts`.

## Risks

- `ILIKE '%q%'` can't use an index; fine at today's sizes. An index would need a migration, which the constraints rule out.
- Backend pytest and Playwright are outside `VERIFY` (see `UNTESTED`).

## Out of scope

- Full-text search, ranking, highlighting, searching other users' items as a normal user.

## Tickets
<!-- filled by /to-tickets -->
