# sb-lab

Systems Builder course lab project.

## Commands

- Run tests: `uv run pytest -q`
- Lint: `uv run ruff check .`
- Type check: `uv run mypy .`
- Run the app: `uv run uvicorn <module>:app --reload`
- Add a dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`
