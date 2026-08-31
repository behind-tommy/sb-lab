# sb-lab

Systems Builder course lab project.

## Commands
- test: `uv run pytest -q`
- lint: `uv run ruff check .`  · format: `uv run ruff format .`
- types: `uv run mypy .`
- run: `uv run uvicorn app.main:app --reload`
- migrate: `uv run alembic upgrade head`
- Add a dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`

## Non-negotiables
- Every endpoint filters by `current_user`. Write the ownership test first (user A → user B's record → 404).
- Every network call has a timeout. Retry only idempotent operations, with backoff.
- Never edit, weaken, skip or delete a test to make it pass. If a test is wrong, stop and say so.
- Secrets come from the environment. `.env` is human-only; `.env.example` holds placeholders.
- Structured JSON logs with a request id on every line.

## Definition of done
1. Tests exist for the new behaviour. 2. `ruff`, `mypy`, `pytest` ran and the output is pasted. 3. New endpoints have ownership checks and tests. 4. Network calls have timeouts. 5. No secrets, no debug flags. 6. A summary of what changed and what was NOT done.

## Workflow
Brainstorm → spec in `docs/specs/` (EARS: WHEN … THE SYSTEM SHALL …) → plan in `docs/plans/` (5–15 min tasks) → I approve → TDD each task on a feature branch → `/sb:review-diff` → PR.

## Code comments

The learner is a product manager, not an engineer. When writing or editing code in this project:

- Every file should open with a one-line comment stating its purpose in plain English (what problem it solves, not what it technically does).
- Every function/method/class should have a short ELI5 comment above it explaining *why it exists* and *what it's for* — assume no prior Python or backend knowledge, define jargon inline.
- Prefer plain language over technical terms; when a technical term is unavoidable, define it in the same comment.
- This overrides the general "don't over-comment" default — in this project, comments are a teaching tool, not clutter.

## Course feedback notes

Whenever the learner gives feedback about the course/lesson design, or you
(the instructor) are surprised by unexpected behavior during a demo or task
that was scripted to go smoothly but didn't — append a TODO entry to
`.sb/course-feedback.md` describing what happened and what should change in
the plugin (`/Users/jw/myOS/ai-learning/systems-builder/plugin/`). Do not
edit the plugin itself unprompted; these are notes for the learner to act on
later.
