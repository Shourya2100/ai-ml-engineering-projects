import os
from pathlib import Path

from dotenv import load_dotenv


def load_env() -> None:
    """Load .env file from the monorepo root directory."""
    repo_root = Path(__file__).resolve().parent.parent
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path)


def get_env(key: str, required: bool = True) -> str | None:
    """Retrieve an environment variable.

    Raises ValueError if required=True and the variable is missing or empty.
    """
    value = os.getenv(key)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value
