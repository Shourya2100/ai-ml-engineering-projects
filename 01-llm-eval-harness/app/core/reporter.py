import sys
from datetime import datetime
from pathlib import Path

import jinja2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from common.logging import get_logger

from app.models.result import EvalReport

logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def generate_report(report: EvalReport) -> str:
    """Render an EvalReport into a self-contained HTML string."""
    loader = jinja2.FileSystemLoader(str(TEMPLATES_DIR))
    env = jinja2.Environment(loader=loader, autoescape=True)
    template = env.get_template("report.html")

    generated_at = datetime.now().strftime("%B %d, %Y at %H:%M:%S")

    html = template.render(report=report, generated_at=generated_at)

    logger.info(
        "Generated HTML report for run '%s' (%d test cases)",
        report.run_id,
        report.total_cases,
    )

    return html
