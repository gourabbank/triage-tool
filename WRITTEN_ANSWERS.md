# Written Answers

## Problem framing

Internal tools teams get a constant stream of requests — some are quick
data pulls, some need real engineering, and many are too vague to act on.
Today that triage happens ad hoc, so requests get lost, duplicated, or
built before anyone confirms they're worth building. This tool gives
requesters a single place to submit a request in plain language,
immediately produces a structured first-pass read for the reviewing team,
and gives that team a queue to triage and track status against. Primary
users: any employee submitting a request, and the internal tools team
reviewing it.

## Architecture

```
[Frontend: TypeScript, compiled to ES modules]
        │  fetch (+ X-Reviewer-Token when configured)
        ▼
[FastAPI backend]
   ├── /requests (POST, open)      → duplicate check → BriefGenerator
   │                                  → validate → persist Request + Brief
   ├── /requests (GET, reviewer)   → list/filter
   ├── /requests/{id} (GET)        → detail
   ├── /requests/{id} (PATCH)      → triage update → audit diff → webhook
   ├── /requests/{id}/audit
   └── /requests/export/csv (open)
        │
        ▼
[SQLite via SQLAlchemy]
   Request ──1:1── Brief
   Request ──1:N── AuditEntry
   Request ──self-FK── duplicate_of
```

Built in phases, each verified against a running Docker container before
the next began: raw CRUD with no AI logic, then mock brief generation,
then triage/audit, then an automated test suite, then the frontend (plain
JS first, converted to TypeScript once the logic was proven), then a real
model integration, then the remaining stretch goals, then deployment.
That ordering was deliberate — isolating each layer meant that when
something broke, it was immediately clear which layer was responsible.

## AI-assisted development

I used Claude throughout, with a deliberate working style: rather than
having Claude generate the whole app for me to inspect afterward, I asked
it to instruct me phase by phase — Claude proposed each step, I typed the
files myself, ran every command, and reported real terminal output back
at each checkpoint before moving on. That meant I could actually explain
every layer of the app, not just review code someone else wrote.

That approach surfaced two categories of AI failure worth naming
honestly. First, environment-specific mistakes: Claude guessed a Groq
model name from general documentation that turned out not to exist on my
actual account; the fix only came from querying `GET /v1/models` directly
against my key, not from better reasoning about docs. Second — and more
interesting — mistakes in Claude's own multi-turn instructions: on at
least two separate occasions, later messages referenced code (a
`BaseBriefGenerator` class, a `generate_mock_brief` function) that had
only been given in an earlier message and never actually made it into the
file I was editing, producing `NameError` crashes that had nothing to do
with my own typing. The fix in both cases was the same: stop accepting
incremental fragments and ask for the complete, self-contained file
instead, which eliminated an entire class of bug outright.

I also hit two genuine Docker/deployment gotchas independent of AI
quality: a stale Docker volume silently preserving an old, incompatible
schema across model changes (`docker compose down` doesn't remove
volumes; `down -v` does), and Render's static-site Build Command field
silently skipping the TypeScript build when left blank, producing a
frontend that served its static shell but never loaded any application
logic. Both were diagnosed the same way every other bug in this project
was: read the actual log or traceback, don't guess.

## Trade-offs

All six stretch goals are implemented, but each is deliberately scoped
down rather than production-hardened: duplicate detection uses lexical
similarity, not embeddings, so paraphrased requests slip through; auth is
one shared reviewer token, not per-user accounts; the webhook is
fire-and-forget with no retry queue. I chose breadth (get every stretch
goal to a genuinely working, tested state) over depth on any single one,
since a partial set of deeply-polished features seemed like a worse
demonstration of range than a complete set of honestly-scoped ones.

**With another week:** swap duplicate detection to embedding similarity;
replace the shared token with real per-user accounts and role-based
access; move webhook delivery to a durable outbox pattern; add pagination
and search to the queue once volume grows past what fits on one screen;
add a persistent disk on the Render deployment so triage data survives
redeploys.

## Production readiness

Before this could be used for real: replace the shared reviewer token
with real authentication and role-based access; move off SQLite to a
managed Postgres instance with backups (SQLite's ephemeral behavior on
Render without a persistent disk is a real gap already surfaced during
deployment, not just a theoretical one); add rate limiting and structured
observability around brief-generation and webhook-delivery failures;
replace the wide-open CORS policy with an explicit allowlist; add cost
monitoring and tighter timeout/retry handling around the Groq integration
beyond the existing mock fallback.
