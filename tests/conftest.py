# Runs before any test file imports the app. The app refuses to start
# without a database address (see app/config.py), but tests like
# test_health.py never actually touch the database — so we hand it a
# fake-but-valid one just to get past that startup check, not to connect.

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
)
