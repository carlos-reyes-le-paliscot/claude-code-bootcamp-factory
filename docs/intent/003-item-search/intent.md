# Intent: Search items

Author: Carlos Reyes

## Problem

Users with more than a page of items scroll to find one. The items page lists the newest 100 with no way to filter, so an older item is effectively lost.

## Proposed outcome

The items page has a search box. Typing filters the list to the user's items that match, and clearing it shows the full list again. Superusers search across all items, as they list all items today.

## Affected users and systems

- All users of the items page.
- This repo only: `GET /items/` in the FastAPI backend, the items page in the React frontend, and the generated API client.

## Constraints

- Keep it small.
- No migration and no new dependency.
- Keep today's ownership rule: a normal user only ever sees their own items.
- `GET /items/` without a search term behaves exactly as today.
- Tests for the search at the API boundary. Existing tests stay green.

## Open questions

- What should a search match: the title only, or the description too?
- Should matching ignore case?
