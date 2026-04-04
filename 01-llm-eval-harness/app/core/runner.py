import time

import anthropic

from app.models.test_case import TestSuite
from app import config as settings

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from common.http import server_error
from common.logging import get_logger

logger = get_logger(__name__)


def run_test_suite(suite: TestSuite) -> list[dict]:
    """Call Claude for each test case in the suite and collect responses."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    results = []

    for test_case in suite.test_cases:
        logger.info("Running test case: %s", test_case.id)

        response_text = _call_claude(client, suite, test_case.prompt)
        results.append({"id": test_case.id, "llm_response": response_text})

    return results


def _call_claude(
    client: anthropic.Anthropic,
    suite: TestSuite,
    prompt: str,
) -> str:
    """Send a prompt to Claude with a single retry on API errors."""
    last_error = None

    for attempt in range(2):
        try:
            message = client.messages.create(
                model=suite.model,
                max_tokens=suite.max_tokens,
                temperature=suite.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except anthropic.APIError as e:
            last_error = e
            if attempt == 0:
                logger.warning("Claude API error (will retry in 2s): %s", e)
                time.sleep(2)

    server_error(f"LLM API call failed: {last_error}")
