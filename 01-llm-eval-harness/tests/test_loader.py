import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from pydantic import ValidationError

from app.core.loader import load_test_suite


VALID_YAML = """
suite_name: "Test Suite"
model: "claude-3-5-haiku-20241022"
test_cases:
  - id: "tc_001"
    description: "A test case"
    prompt: "Summarise this text"
    criteria:
      - type: max_length
        value: 150
"""

YAML_WITH_INPUT = """
suite_name: "Input Suite"
model: "claude-3-5-haiku-20241022"
test_cases:
  - id: "tc_001"
    description: "Test with input template"
    prompt: "Summarise: {{ input }}"
    input: "The sky is blue."
    criteria:
      - type: max_length
        value: 100
"""

YAML_NO_INPUT = """
suite_name: "No Input Suite"
model: "claude-3-5-haiku-20241022"
test_cases:
  - id: "tc_001"
    description: "Static prompt"
    prompt: "What is 2 + 2?"
    criteria:
      - type: contains_keywords
        keywords: ["4"]
"""

YAML_MISSING_SUITE_NAME = """
model: "claude-3-5-haiku-20241022"
test_cases:
  - id: "tc_001"
    description: "A test"
    prompt: "Hello"
    criteria:
      - type: max_length
        value: 100
"""

YAML_MISSING_TEST_CASES = """
suite_name: "Empty Suite"
model: "claude-3-5-haiku-20241022"
"""


def test_valid_yaml_parses_to_test_suite():
    suite = load_test_suite(VALID_YAML)
    assert suite.suite_name == "Test Suite"
    assert suite.model == "claude-3-5-haiku-20241022"
    assert suite.max_tokens == 500
    assert suite.temperature == 0.0
    assert len(suite.test_cases) == 1
    assert suite.test_cases[0].id == "tc_001"
    assert suite.test_cases[0].criteria[0].type == "max_length"
    assert suite.test_cases[0].criteria[0].value == 150


def test_input_renders_into_prompt():
    suite = load_test_suite(YAML_WITH_INPUT)
    assert "The sky is blue." in suite.test_cases[0].prompt
    assert "{{ input }}" not in suite.test_cases[0].prompt


def test_no_input_leaves_prompt_unchanged():
    suite = load_test_suite(YAML_NO_INPUT)
    assert suite.test_cases[0].prompt == "What is 2 + 2?"


def test_missing_suite_name_raises_validation_error():
    with pytest.raises(ValidationError):
        load_test_suite(YAML_MISSING_SUITE_NAME)


def test_missing_test_cases_raises_validation_error():
    with pytest.raises(ValidationError):
        load_test_suite(YAML_MISSING_TEST_CASES)
