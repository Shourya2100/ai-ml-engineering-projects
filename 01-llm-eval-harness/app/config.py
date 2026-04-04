import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common.config import get_env, load_env

load_env()

ANTHROPIC_API_KEY: str = get_env("ANTHROPIC_API_KEY", required=False) or ""
DEFAULT_MODEL: str = get_env("DEFAULT_MODEL", required=False) or "claude-3-5-haiku-20241022"
MAX_TOKENS_DEFAULT: int = int(get_env("MAX_TOKENS_DEFAULT", required=False) or "500")
REPORTS_DIR: str = get_env("REPORTS_DIR", required=False) or "reports"
LOG_LEVEL: str = get_env("LOG_LEVEL", required=False) or "INFO"
