import sys
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from common.http import bad_request, not_found, server_error
from common.logging import get_logger

from app import config as settings
from app.core.loader import load_test_suite
from app.core.reporter import generate_report
from app.core.runner import run_test_suite
from app.core.scorer import score_test_case
from app.models.result import EvalReport

logger = get_logger(__name__)

router = APIRouter()


@router.post("/run")
async def run_eval(file: UploadFile):
    text = (await file.read()).decode("utf-8")

    try:
        suite = load_test_suite(text)
    except ValidationError as e:
        bad_request(f"Invalid test suite: {e}")
    except Exception as e:
        bad_request(f"Failed to parse YAML: {e}")

    raw_results = run_test_suite(suite)

    test_results = []
    for raw, tc in zip(raw_results, suite.test_cases):
        test_results.append(score_test_case(raw, tc))

    passed = sum(1 for r in test_results if r.passed)
    failed = len(test_results) - passed
    overall_score = (passed / len(test_results)) * 100 if test_results else 0.0

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    report = EvalReport(
        run_id=run_id,
        suite_name=suite.suite_name,
        model=suite.model,
        total_cases=len(test_results),
        passed=passed,
        failed=failed,
        overall_score=round(overall_score, 1),
        report_url=f"/eval/report/{run_id}",
        results=test_results,
    )

    reports_dir = Path(settings.REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)
    html = generate_report(report)
    (reports_dir / f"{run_id}.html").write_text(html)

    logger.info("Eval run '%s' complete: %.1f%% overall", run_id, overall_score)

    return report


@router.get("/report/{run_id}")
async def get_report(run_id: str):
    report_path = Path(settings.REPORTS_DIR) / f"{run_id}.html"

    if not report_path.exists():
        not_found(f"Report '{run_id}' not found")

    html = report_path.read_text()
    return HTMLResponse(content=html)
