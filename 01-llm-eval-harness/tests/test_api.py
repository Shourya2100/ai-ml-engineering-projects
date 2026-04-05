import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_YAML = """\
suite_name: "Test Suite"
model: "claude-3-5-haiku-20241022"
max_tokens: 100
test_cases:
  - id: "tc_001"
    description: "Simple test"
    prompt: "Say hello"
    criteria:
      - type: max_length
        value: 500
      - type: contains_keywords
        keywords: ["hello"]
"""

INVALID_YAML = """\
model: "claude-3-5-haiku-20241022"
test_cases: "not a list"
"""


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["project"] == "llm-eval-harness"


def _mock_claude_response(text: str) -> MagicMock:
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=text)]
    return mock_message


@patch("app.core.runner.anthropic.Anthropic")
def test_eval_run_with_valid_yaml(mock_anthropic_cls, tmp_path):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_claude_response("hello world")
    mock_anthropic_cls.return_value = mock_client

    with patch("app.api.routes.eval.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "fake-key"
        mock_settings.REPORTS_DIR = str(tmp_path)

        response = client.post(
            "/eval/run",
            files={"file": ("test.yaml", VALID_YAML, "text/yaml")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["suite_name"] == "Test Suite"
    assert data["total_cases"] == 1
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "tc_001"
    assert "criteria_results" in data["results"][0]


def test_eval_run_with_invalid_yaml():
    response = client.post(
        "/eval/run",
        files={"file": ("bad.yaml", INVALID_YAML, "text/yaml")},
    )
    assert response.status_code == 400


def test_get_report_nonexistent_returns_404():
    response = client.get("/eval/report/run_nonexistent_000000")
    assert response.status_code == 404
