# AI Usage Log

## Tool used
Claude (Sonnet 5), via claude.ai chat. This project was built with Claude
acting as an instructor: Claude proposed a phased build plan, gave me
code and commands one step at a time, and I typed every file, ran every
command, and reported real terminal output back before moving on. The
raw prompt-by-prompt history is published separately as a Claude
artifact; this file is the narrated summary.

## Build phases and what happened at each

**Phase 1 — Docker-native skeleton.** Minimal FastAPI health check,
Dockerfile, docker-compose.yml, verified with `curl localhost:8000/health`
before any real logic existed.

**Phase 2 — Database layer.** SQLAlchemy models, a bare `POST`/`GET
/requests`. Hit a real SQLite gotcha here: a stale Docker volume from an
earlier run preserved an incompatible schema, causing a `NOT NULL
constraint` error that had nothing to do with the current code.
`docker compose down -v` (not just `down`) was the fix — a genuine Docker
lesson, not an AI mistake.

**Phase 3 — Mock brief generation.** Wired a deterministic mock generator
into the create-request flow. Hit an AI mistake here: Claude's own
instructions omitted a `created_at` column on the `Brief` model that a
later step assumed existed, causing an `AttributeError`. Fixed by adding
the missing column — a reminder that AI-generated instructions need the
same verification as AI-generated code.

**Phase 4 — Triage and audit.** `PATCH` endpoint with field-level diffing
into an audit log, `GET` for the audit trail. Worked cleanly on the first
real attempt.

**Phase 5 — Automated tests.** Six tests covering the routes built so far.
Uncovered a real bug in test isolation (two test files both reassigning
FastAPI's global `dependency_overrides` at import time) and a genuine
HTTP-semantics point I hadn't considered: a missing route returns 405, not
404, for a URL pattern that exists under a different method.

**Phase 6 — Frontend, plain JS first.** Deliberately un-typed to prove the
`fetch()` wiring before adding type safety. Hit the expected CORS failure
(no middleware configured yet) — diagnosed via the browser console, which
never showed up in server logs.

**Phase 7 — TypeScript conversion.** Converted the working JS to strict
TypeScript. Learned that `tsc` run with no `tsconfig.json` in scope
silently prints help text instead of erroring — easy to misread as
something broken with the code rather than a working-directory mistake.

**Phase 8 — Real Groq integration.** Queried Groq's own `GET /v1/models`
against my actual account before writing any code, rather than guessing a
model name from documentation — this avoided a long, speculative
debugging thread entirely. Still hit two AI-instruction mistakes here
(fragments referencing code from earlier messages that hadn't made it
into the actual file), which is what led to adopting "give me the
complete file" as a standing practice going forward rather than
continuing to accept incremental patches.

**Phase 9 — Remaining stretch goals.** Duplicate detection, reviewer
auth, webhook stub, CSV export, eval script — implemented as small,
independent modules, each covered by its own test. All 11 tests passing
confirmed the full project as a coherent whole, not just individually
correct pieces.

**Phase 10 — Frontend completion and redesign.** Built out the full
submit/queue/detail/triage/audit UI, then a dedicated visual design pass
(color system, typography, priority badges) once the functional version
was confirmed working — deliberately sequenced after correctness, not
before.

**Phase 11 — Deployment.** Hit a SQLite-path issue specific to Render's
filesystem (no volume/path handling for a non-Docker host, since the
local Docker Compose volume mount doesn't exist there) and a Render
Build Command trap (a blank Build Command field silently skips the
frontend build rather than erroring). Both diagnosed and fixed the same
way as everything else: reading the actual build/runtime log rather than
guessing.

## Where AI helped vs. where I intervened

AI was strong at generating correct boilerplate quickly and at proposing
the right *next diagnostic command* when something broke (log inspection,
querying an external API's own model list, checking Docker Compose
service status) rather than guessing a fix outright. AI was weak at
maintaining consistency across its own multi-turn instructions — several
bugs in this project were caused by Claude's own earlier guidance being
incomplete by the time a later step assumed it was in place, which is a
different failure mode from "the AI's code was wrong" and one I hadn't
anticipated going in.

My own contribution was running every single command myself, actually
reading tracebacks rather than re-pasting the first error I saw, and
making the judgment calls at each checkpoint about whether to move
forward or dig further — including a live decision to prioritize
completing the frontend's core requirements before layering on optional
stretch features, since that gap mattered more against the actual
assessment brief than any single stretch goal would have.

## Overall reflection

Building it this way — phase by phase, with me running every command and
reporting real output — took longer than having AI generate the whole
thing upfront, but produced a version I can actually explain end to end,
including *why* each Docker/Render/TypeScript gotcha happened, not just
that it got fixed. That's the more defensible story for the follow-up
interview this assessment explicitly includes.
