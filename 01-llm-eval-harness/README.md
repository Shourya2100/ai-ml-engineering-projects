# LLM Eval Harness

A lightweight backend tool for testing LLM prompts. Define test cases in YAML, run them against Claude, score the responses with deterministic criteria, and generate a shareable HTML report. Built to answer one question: *"Is my prompt actually working — and is version 2 better than version 1?"*

## Quick Start

**1. Clone and navigate**

```bash
git clone https://github.com/Shourya2100/ai-ml-engineering-projects.git
cd ai-ml-engineering-projects
```

**2. Create a virtual environment and install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-common.txt -r 01-llm-eval-harness/requirements.txt
```

**3. Set your API key**

```bash
cp 01-llm-eval-harness/.env.example .env
# Edit .env and add your Anthropic API key
```

**4. Start the server**

```bash
cd 01-llm-eval-harness
uvicorn app.main:app --reload
```

**5. Run an eval**

```bash
curl -X POST http://localhost:8000/eval/run \
  -F "file=@test_suites/summarisation.yaml"
```

The JSON response includes a `report_url` — open it in your browser to view the HTML report.

## Writing Test Suites

Test suites are YAML files that define prompts, inputs, and scoring criteria:

```yaml
suite_name: "My Test Suite"
model: "claude-3-5-haiku-20241022"
max_tokens: 300
temperature: 0.0

test_cases:
  - id: "tc_001"
    description: "What this test checks"
    prompt: |
      Your prompt here. Use {{ input }} to inject test data.
    input: |
      The text you want to test against.
    criteria:
      - type: max_length
        value: 150
      - type: contains_keywords
        keywords: ["important", "terms"]
```

## Scoring Criteria Reference

| Criterion | Parameters | Description |
|---|---|---|
| `max_length` | `value: int` | Response must be under N characters |
| `min_length` | `value: int` | Response must be over N characters |
| `contains_keywords` | `keywords: list` | All listed keywords must appear (case-insensitive) |
| `excludes_keywords` | `keywords: list` | None of the listed keywords may appear (case-insensitive) |
| `sentence_count` | `expected: int` | Response must contain exactly N sentences |
| `json_valid` | — | Response must be parseable as valid JSON |
| `json_has_keys` | `keys: list` | Response JSON must contain the specified keys |
| `regex_match` | `pattern: str` | Response must match the given regex pattern |

Each criterion returns pass/fail with a reason. A test case passes only if **all** its criteria pass. Overall score = `passed_criteria / total_criteria × 100`.

## Reading the Report

The HTML report shows:

- **Header** — Run ID, suite name, model, timestamp, and overall score (color-coded green/yellow/red)
- **Summary bar** — Total test cases, passed count, failed count
- **Per test case** — Pass/fail badge, score percentage, Claude's full response, and a criteria breakdown table showing exactly what passed and what didn't

Reports are saved to the `reports/` directory and can be accessed at `GET /eval/report/{run_id}`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/eval/run` | Upload a YAML test suite, run it, return JSON report |
| `GET` | `/eval/report/{run_id}` | Fetch the saved HTML report |
| `GET` | `/health` | Health check |

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI | REST API |
| Anthropic SDK | Claude API calls |
| PyYAML | Parse YAML test suites |
| Jinja2 | Render HTML reports |
| Pydantic | Request/response validation |
| Pytest | Unit and integration tests |

## Running Tests

```bash
cd 01-llm-eval-harness
python -m pytest tests/ -v
```
