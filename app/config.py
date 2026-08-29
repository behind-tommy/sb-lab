# This file answers one question: "where does the app find its secrets/config?"
# Right now that's just the database address, read from an environment variable
# (a value set outside the code, e.g. by Railway or your .env file) called DATABASE_URL.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # pydantic-settings auto-fills each field below from an env var of the same
    # name (case-insensitive), or from the .env file if the var isn't set.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No default value here on purpose: if DATABASE_URL is missing, creating
    # Settings() below crashes immediately with a clear error, instead of the
    # app starting fine and only failing later when it actually needs the DB.
    database_url: str


# Created once, at import time, so every other file can just do
# `from app.config import settings` and reuse the same loaded config.
settings = Settings()  # type: ignore[call-arg]
