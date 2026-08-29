# sb-lab

Systems Builder course lab project.

## Commands

- Run tests: `uv run pytest -q`
- Lint: `uv run ruff check .`
- Type check: `uv run mypy .`
- Run the app: `uv run uvicorn <module>:app --reload`
- Add a dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`

## Code comments

The learner is a product manager, not an engineer. When writing or editing code in this project:

- Every file should open with a one-line comment stating its purpose in plain English (what problem it solves, not what it technically does).
- Every function/method/class should have a short ELI5 comment above it explaining *why it exists* and *what it's for* — assume no prior Python or backend knowledge, define jargon inline.
- Prefer plain language over technical terms; when a technical term is unavoidable, define it in the same comment.
- This overrides the general "don't over-comment" default — in this project, comments are a teaching tool, not clutter.
