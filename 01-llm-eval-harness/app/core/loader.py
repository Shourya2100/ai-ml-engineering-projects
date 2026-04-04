import yaml
from jinja2 import Environment

from app.models.test_case import TestSuite

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from common.logging import get_logger

logger = get_logger(__name__)


def load_test_suite(file_content: str) -> TestSuite:
    """Parse YAML content into a validated TestSuite, rendering any input templates."""
    parsed = yaml.safe_load(file_content)
    suite = TestSuite(**parsed)

    jinja_env = Environment()
    for test_case in suite.test_cases:
        if test_case.input is not None:
            template = jinja_env.from_string(test_case.prompt)
            test_case.prompt = template.render(input=test_case.input)

    logger.info(
        "Loaded suite '%s' with %d test case(s)",
        suite.suite_name,
        len(suite.test_cases),
    )

    return suite
