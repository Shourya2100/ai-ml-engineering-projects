from pydantic import BaseModel


class CriterionResult(BaseModel):
    type: str
    passed: bool
    reason: str


class TestResult(BaseModel):
    id: str
    description: str
    passed: bool
    score: float
    llm_response: str
    criteria_results: list[CriterionResult]


class EvalReport(BaseModel):
    run_id: str
    suite_name: str
    model: str
    total_cases: int
    passed: int
    failed: int
    overall_score: float
    report_url: str
    results: list[TestResult]
