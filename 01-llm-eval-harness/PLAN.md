# PLAN.md — LLM Eval Harness
# Project 1 of 4 — ai-ml-engineering-projects monorepo

## Project Overview

A lightweight backend tool that lets you define test cases for LLM prompts in YAML,
run them against Claude, score the results automatically, and generate a human-readable
HTML report. The goal is to answer one question every AI engineering team has: "Is my
prompt actually working — and is version 2 better than version 1?"

This is Project 1 of a 4-part personal series on AI and ML engineering, all living
in a single monorepo called `ai-ml-engineering-projects`.

---

## Before You Start

The GitHub repo must already exist and be cloned locally before running this plan.
Steps the developer does manually (not part of this plan):

1. Create a new public repo on GitHub named `ai-ml-engineering-projects`
2. Clone it: `git clone https://github.com/<your-username>/ai-ml-engineering-projects`
3. Open the repo root in Cursor
4. Hand this PLAN.md to the agent and say: "Build phase by phase. Ask me before
   moving to the next phase."

---

## Monorepo Structure

This project lives inside a monorepo that will eventually hold 4 projects.
Only the folders needed for Project 1 are created now. The rest are added later.

```
ai-ml-engineering-projects/
├── .gitignore                         ← Covers all projects
├── requirements-common.txt            ← Shared deps across all projects
│
├── common/                            ← Shared Python utilities (not AI tooling)
│   ├── __init__.py
│   ├── config.py                      ← Shared env var loading
│   ├── logging.py                     ← Shared logging setup
│   └── http.py                        ← Shared FastAPI error helpers
│
└── 01-llm-eval-harness/               ← This project
    ├── README.md
    ├── PLAN.md
    ├── requirements.txt
    ├── .env.example
    └── app/
```

The following folders will be created in future projects. Do NOT create them now:
- `02-data-drift-detective/`
- `03-rag-pipeline/`
- `04-feature-store/`

### Why `common/` exists

`common/` holds plain Python utilities — logging, config loading, and HTTP error
helpers — that every project in the monorepo will reuse. This avoids duplicating
the same boilerplate across 4 project folders. It is not AI tooling.

All imports from common use: `from common.logging import get_logger`

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| FastAPI | 0.111+ | REST API layer |
| Uvicorn | 0.29+ | ASGI server |
| Anthropic SDK | 0.25+ | Claude API calls |
| PyYAML | 6.0+ | Parse test case definitions |
| Jinja2 | 3.1+ | Render HTML report |
| Pydantic | 2.x | Request / response validation |
| Pytest | 8.x | Unit tests |
| httpx | 0.27+ | Async HTTP client (for tests) |

---

## Full Project Structure

```
ai-ml-engineering-projects/
│
├── .gitignore
├── requirements-common.txt            ← fastapi, uvicorn, pydantic, anthropic, python-dotenv
│
├── common/
│   ├── __init__.py
│   ├── config.py                      ← load_env(), get_env(key, required)
│   ├── logging.py                     ← get_logger(name) → configured Logger
│   └── http.py                        ← bad_request(), not_found(), server_error()
│
└── 01-llm-eval-harness/
    ├── README.md
    ├── PLAN.md
    ├── requirements.txt               ← pyyaml, jinja2, httpx, pytest, pytest-asyncio
    ├── .env.example
    │
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                    ← FastAPI app entrypoint
    │   ├── config.py                  ← Project-specific settings, extends common/config.py
    │   │
    │   ├── api/
    │   │   ├── __init__.py
    │   │   └── routes/
    │   │       ├── __init__.py
    │   │       ├── eval.py            ← POST /eval/run, GET /eval/report/{run_id}
    │   │       └── health.py          ← GET /health
    │   │
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── loader.py              ← Load + validate YAML test suite files
    │   │   ├── runner.py              ← Call Claude per test case
    │   │   ├── scorer.py              ← Score responses against criteria
    │   │   └── reporter.py            ← Render HTML report
    │   │
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── test_case.py           ← Pydantic: TestCase, TestSuite
    │   │   └── result.py              ← Pydantic: TestResult, EvalReport
    │   │
    │   └── templates/
    │       └── report.html            ← Jinja2 HTML report template
    │
    ├── test_suites/
    │   ├── summarisation.yaml
    │   └── classification.yaml
    │
    └── tests/
        ├── __init__.py
        ├── test_loader.py
        ├── test_scorer.py
        └── test_api.py
```

---

## Core Concepts

### Test Suite (YAML)

```yaml
# 01-llm-eval-harness/test_suites/summarisation.yaml

suite_name: "Summarisation Quality"
model: "claude-3-5-haiku-20241022"
max_tokens: 300
temperature: 0.0

test_cases:
  - id: "tc_001"
    description: "Summarise a news article in 2 sentences"
    prompt: |
      Summarise the following article in exactly 2 sentences.
      Article: {{ input }}
    input: |
      The Federal Reserve raised interest rates by 0.25% on Wednesday,
      citing persistent inflation above its 2% target. Economists expect
      at least one more hike before the end of the year. Markets reacted
      negatively, with the S&P 500 dropping 1.2% by close of trading.
    criteria:
      - type: max_length
        value: 150
      - type: contains_keywords
        keywords: ["Federal Reserve", "inflation"]
      - type: sentence_count
        expected: 2

  - id: "tc_002"
    description: "Summarise without losing key numbers"
    prompt: |
      Summarise the following in 1 sentence, keeping all numerical figures.
      Text: {{ input }}
    input: |
      The company reported Q3 revenue of $4.2 billion, up 18% year-on-year,
      with net profit margins improving to 22% from 19% last quarter.
    criteria:
      - type: contains_keywords
        keywords: ["4.2", "18%", "22%"]
      - type: max_length
        value: 120
```

### Scoring Criteria (Supported Types)

| Criterion | Description |
|---|---|
| `max_length` | Response must be under N characters |
| `min_length` | Response must be over N characters |
| `contains_keywords` | All listed keywords must appear in response |
| `excludes_keywords` | None of the listed keywords may appear |
| `sentence_count` | Response must contain exactly N sentences |
| `json_valid` | Response must be parseable as valid JSON |
| `json_has_keys` | Response JSON must contain specified keys |
| `regex_match` | Response must match a given regex pattern |

Each criterion returns `passed: bool` and `reason: str`.
Overall score = `passed_criteria / total_criteria * 100`.

---

## API Design

### POST `/eval/run`

**Request:** `multipart/form-data` — `file: <test_suite.yaml>`

**Response:**
```json
{
  "run_id": "run_20260403_143021",
  "suite_name": "Summarisation Quality",
  "model": "claude-3-5-haiku-20241022",
  "total_cases": 2,
  "passed": 1,
  "failed": 1,
  "overall_score": 50.0,
  "report_url": "/eval/report/run_20260403_143021",
  "results": [
    {
      "id": "tc_001",
      "description": "Summarise a news article in 2 sentences",
      "passed": true,
      "score": 100.0,
      "llm_response": "The Federal Reserve raised rates...",
      "criteria_results": [
        { "type": "max_length", "passed": true, "reason": "Length 132 <= 150" },
        { "type": "contains_keywords", "passed": true, "reason": "All keywords found" },
        { "type": "sentence_count", "passed": true, "reason": "Found 2 sentences" }
      ]
    }
  ]
}
```

### GET `/eval/report/{run_id}`

Returns the rendered HTML report. This is the shareable output.

### GET `/health`

Returns `{ "status": "ok", "project": "llm-eval-harness" }`.

---

## Implementation Phases

Work through these in order. Each phase = one Git branch + one commit.
Ask the developer before moving to the next phase.

---

### Phase 1 — Monorepo Scaffold
**Branch:** `phase/1-monorepo-scaffold`

**At the repo root:**
- [ ] Create `.gitignore` covering: `__pycache__/`, `*.pyc`, `.env`, `venv/`,
      `.venv/`, `reports/`, `.DS_Store`, `*.egg-info/`
- [ ] Create `requirements-common.txt`:
      `fastapi`, `uvicorn[standard]`, `pydantic`, `anthropic`, `python-dotenv`
- [ ] Create `common/__init__.py` (empty)
- [ ] Create `common/config.py`
  - `load_env()` — loads `.env` from repo root via `python-dotenv`
  - `get_env(key: str, required: bool = True) -> str | None`
    raises `ValueError` if required and missing
- [ ] Create `common/logging.py`
  - `get_logger(name: str) -> logging.Logger`
  - Format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`
  - Level from `LOG_LEVEL` env var, default `INFO`
- [ ] Create `common/http.py`
  - `bad_request(detail: str)` → `HTTPException(400)`
  - `not_found(detail: str)` → `HTTPException(404)`
  - `server_error(detail: str)` → `HTTPException(500)`

**Inside `01-llm-eval-harness/`:**
- [ ] Create `.env.example`: `ANTHROPIC_API_KEY=your_key_here`
- [ ] Create `requirements.txt`:
      `pyyaml`, `jinja2`, `httpx`, `pytest`, `pytest-asyncio`
- [ ] Create `app/__init__.py`
- [ ] Create `app/config.py`
  - Calls `load_env()` from `common.config`
  - Exposes: `ANTHROPIC_API_KEY`, `DEFAULT_MODEL`, `MAX_TOKENS_DEFAULT`,
    `REPORTS_DIR` (default `"reports"`), `LOG_LEVEL`
- [ ] Create `app/main.py`
  - FastAPI app, title `"LLM Eval Harness"`
  - Registers health router
  - CORS middleware, allow all origins
- [ ] Create `app/api/__init__.py`, `app/api/routes/__init__.py`
- [ ] Create `app/api/routes/health.py`
  - `GET /health` → `{"status": "ok", "project": "llm-eval-harness"}`

**Done when:** `uvicorn app.main:app --reload` (run from inside `01-llm-eval-harness/`)
starts cleanly and `curl localhost:8000/health` returns 200.

---

### Phase 2 — Models
**Branch:** `phase/2-models`

- [ ] Create `app/models/__init__.py`
- [ ] Create `app/models/test_case.py`
  - `ScoringCriterion(BaseModel)`:
    `type: str`, `value: int | None = None`, `keywords: list[str] | None = None`,
    `expected: int | None = None`, `pattern: str | None = None`,
    `keys: list[str] | None = None`
  - `TestCase(BaseModel)`:
    `id: str`, `description: str`, `prompt: str`, `input: str | None = None`,
    `criteria: list[ScoringCriterion]`
  - `TestSuite(BaseModel)`:
    `suite_name: str`, `model: str`, `max_tokens: int = 500`,
    `temperature: float = 0.0`, `test_cases: list[TestCase]`
- [ ] Create `app/models/result.py`
  - `CriterionResult(BaseModel)`: `type: str`, `passed: bool`, `reason: str`
  - `TestResult(BaseModel)`:
    `id: str`, `description: str`, `passed: bool`, `score: float`,
    `llm_response: str`, `criteria_results: list[CriterionResult]`
  - `EvalReport(BaseModel)`:
    `run_id: str`, `suite_name: str`, `model: str`, `total_cases: int`,
    `passed: int`, `failed: int`, `overall_score: float`, `report_url: str`,
    `results: list[TestResult]`

**Done when:** All models import and instantiate without errors.

---

### Phase 3 — Loader
**Branch:** `phase/3-loader`

- [ ] Create `app/core/__init__.py`
- [ ] Create `app/core/loader.py`
  - `from common.logging import get_logger`
  - `load_test_suite(file_content: str) -> TestSuite`
    - Parse with `yaml.safe_load`
    - Validate with `TestSuite(**parsed)` — let Pydantic raise `ValidationError`
    - For each test case: if `input` is set, render `{{ input }}` in the prompt
      using `jinja2.Environment().from_string(prompt).render(input=input)`
    - Log suite name and test case count at INFO

- [ ] Create `tests/__init__.py`
- [ ] Create `tests/test_loader.py`
  - Valid YAML parses to `TestSuite` with correct fields
  - `{{ input }}` renders correctly into the prompt
  - Missing `suite_name` raises `ValidationError`
  - Missing `test_cases` raises `ValidationError`
  - Test case with no `input` leaves prompt unchanged

**Done when:** `pytest tests/test_loader.py` passes.

---

### Phase 4 — Runner
**Branch:** `phase/4-runner`

- [ ] Create `app/core/runner.py`
  - `from common.logging import get_logger`
  - `from common.http import server_error`
  - `run_test_suite(suite: TestSuite) -> list[dict]`
    - Init `anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)`
    - For each test case:
      - Log `"Running test case: {id}"` at INFO
      - Call Claude:
        ```python
        message = client.messages.create(
            model=suite.model,
            max_tokens=suite.max_tokens,
            temperature=suite.temperature,
            messages=[{"role": "user", "content": test_case.prompt}]
        )
        response_text = message.content[0].text
        ```
      - On `anthropic.APIError`: log at WARNING, wait 2s, retry once
      - If retry fails: `server_error("LLM API call failed: {error}")`
      - Append `{"id": test_case.id, "llm_response": response_text}`
    - Return results list

**Note:** Synchronous only — no async for MVP.

**Done when:** Runner returns LLM responses for each test case when called manually.

---

### Phase 5 — Scorer
**Branch:** `phase/5-scorer`

- [ ] Create `app/core/scorer.py`
  - `from common.logging import get_logger`
  - Private functions (each returns `CriterionResult`):
    - `_check_max_length(response, value)`
    - `_check_min_length(response, value)`
    - `_check_contains_keywords(response, keywords)` — case-insensitive
    - `_check_excludes_keywords(response, keywords)` — case-insensitive
    - `_check_sentence_count(response, expected)` — split on `.!?`, count non-empty
    - `_check_json_valid(response)` — try `json.loads`
    - `_check_json_has_keys(response, keys)` — parse JSON, check keys
    - `_check_regex_match(response, pattern)` — `bool(re.search(...))`
  - `score_response(response: str, criteria: list[ScoringCriterion]) -> list[CriterionResult]`
    - Dispatches to correct function per `criterion.type`
    - Raises `ValueError` for unknown type
  - `score_test_case(run_result: dict, test_case: TestCase) -> TestResult`
    - Calls `score_response`
    - `score = (passing / total) * 100`
    - `passed = (score == 100.0)`

- [ ] Create `tests/test_scorer.py`
  - One pass and one fail test per criterion type
  - Unknown criterion type raises `ValueError`
  - 2 passing + 1 failing = score of 66.7

**Done when:** `pytest tests/test_scorer.py` passes.

---

### Phase 6 — Reporter
**Branch:** `phase/6-reporter`

- [ ] Create `app/templates/report.html`
  - Header: run_id, suite_name, model, generated_at, overall score
  - Summary: total | passed (green) | failed (red)
  - Per test: ID, description, pass/fail badge, score, LLM response in `<pre>`,
    criteria table (type | passed | reason)
  - Inline `<style>` only — no external CSS, no JS, no CDN
  - Clean and screenshot-ready for LinkedIn

- [ ] Create `app/core/reporter.py`
  - `from common.logging import get_logger`
  - `generate_report(report: EvalReport) -> str`
    - `jinja2.FileSystemLoader` pointing at `app/templates/`
    - Render with `report=report`, `generated_at=datetime.now().strftime(...)`
    - Return HTML string

**Done when:** Output renders correctly in a browser with no broken layout.

---

### Phase 7 — API Routes and Integration
**Branch:** `phase/7-api`

- [ ] Create `app/api/routes/eval.py`
  - `from common.http import bad_request, not_found, server_error`
  - `from common.logging import get_logger`
  - `POST /eval/run`
    - Accept `file: UploadFile`
    - Decode: `text = (await file.read()).decode("utf-8")`
    - `loader.load_test_suite(text)` — catch `ValidationError` → `bad_request()`
    - `runner.run_test_suite(suite)`
    - `scorer.score_test_case()` for each result
    - `run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"`
    - Assemble `EvalReport`
    - Save HTML report to `{REPORTS_DIR}/{run_id}.html` (create dir if missing)
    - Return `EvalReport` as JSON
  - `GET /eval/report/{run_id}`
    - File missing → `not_found()`
    - Return `HTMLResponse(content=html)`
- [ ] Register eval router in `app/main.py` with prefix `/eval`
- [ ] Create `tests/test_api.py`
  - `GET /health` → 200
  - `POST /eval/run` with valid YAML → 200, correct JSON shape
  - `POST /eval/run` with invalid YAML → 400
  - `GET /eval/report/{nonexistent_id}` → 404

**Done when:** Full end-to-end run works via curl or Postman.

---

### Phase 8 — Sample Test Suites and README
**Branch:** `phase/8-samples-and-docs`

- [ ] Create `test_suites/summarisation.yaml` — as per the example in this plan
- [ ] Create `test_suites/classification.yaml`
  - Sentiment classification test cases (positive / negative / neutral)
  - Use `contains_keywords` and `regex_match` criteria
- [ ] Write `01-llm-eval-harness/README.md`
  - What it does (1 paragraph)
  - Quick start (5 steps: clone → install → env → run → test)
  - YAML criteria reference table
  - How to read the report
  - Tech stack table

**Done when:** A new developer can clone and run in under 5 minutes.

---

## Error Handling Rules

- Invalid YAML → HTTP 400 via `bad_request()` from `common.http`
- Missing report → HTTP 404 via `not_found()` from `common.http`
- Claude API failure after retry → HTTP 502 via `server_error()` from `common.http`
- All other errors → HTTP 500 via `server_error()`
- Never expose raw tracebacks to the client
- Use `get_logger()` from `common.logging` everywhere — no bare `print()` statements

---

## Environment Variables

```
ANTHROPIC_API_KEY=<your key>                    # Required
DEFAULT_MODEL=claude-3-5-haiku-20241022         # Optional
MAX_TOKENS_DEFAULT=500                           # Optional
REPORTS_DIR=reports                              # Optional, default "reports"
LOG_LEVEL=INFO                                   # Optional, default INFO
```

---

## What Is NOT In Scope

- No database — results live in memory and on disk as HTML only
- No authentication
- No async LLM calls — synchronous is fine for MVP
- No frontend UI
- No Docker
- No OpenAI support — Claude only
- No root `README.md` for the monorepo
- No `02-data-drift-detective/`, `03-rag-pipeline/`, or `04-feature-store/` folders

---

## Definition of Done

1. `POST /eval/run` with `summarisation.yaml` returns a valid JSON report
2. `GET /eval/report/{run_id}` returns clean HTML, screenshot-ready for LinkedIn
3. All tests pass: `pytest 01-llm-eval-harness/tests/`
4. `common/` utilities used consistently — no duplicated config or logging code
5. `01-llm-eval-harness/README.md` complete — runnable in under 5 minutes
6. One meaningful commit per phase pushed to personal GitHub
