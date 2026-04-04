import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from common.logging import get_logger

from app.models.result import CriterionResult, TestResult
from app.models.test_case import ScoringCriterion, TestCase

logger = get_logger(__name__)

_CRITERION_DISPATCH = {}


def _register(criterion_type: str):
    def decorator(fn):
        _CRITERION_DISPATCH[criterion_type] = fn
        return fn
    return decorator


@_register("max_length")
def _check_max_length(response: str, criterion: ScoringCriterion) -> CriterionResult:
    length = len(response)
    passed = length <= criterion.value
    return CriterionResult(
        type="max_length",
        passed=passed,
        reason=f"Length {length} {'<=' if passed else '>'} {criterion.value}",
    )


@_register("min_length")
def _check_min_length(response: str, criterion: ScoringCriterion) -> CriterionResult:
    length = len(response)
    passed = length >= criterion.value
    return CriterionResult(
        type="min_length",
        passed=passed,
        reason=f"Length {length} {'>=' if passed else '<'} {criterion.value}",
    )


@_register("contains_keywords")
def _check_contains_keywords(response: str, criterion: ScoringCriterion) -> CriterionResult:
    response_lower = response.lower()
    missing = [kw for kw in criterion.keywords if kw.lower() not in response_lower]
    passed = len(missing) == 0
    reason = "All keywords found" if passed else f"Missing keywords: {missing}"
    return CriterionResult(type="contains_keywords", passed=passed, reason=reason)


@_register("excludes_keywords")
def _check_excludes_keywords(response: str, criterion: ScoringCriterion) -> CriterionResult:
    response_lower = response.lower()
    found = [kw for kw in criterion.keywords if kw.lower() in response_lower]
    passed = len(found) == 0
    reason = "No excluded keywords found" if passed else f"Found excluded keywords: {found}"
    return CriterionResult(type="excludes_keywords", passed=passed, reason=reason)


@_register("sentence_count")
def _check_sentence_count(response: str, criterion: ScoringCriterion) -> CriterionResult:
    sentences = [s.strip() for s in re.split(r"[.!?]", response) if s.strip()]
    count = len(sentences)
    passed = count == criterion.expected
    return CriterionResult(
        type="sentence_count",
        passed=passed,
        reason=f"Found {count} sentence(s), expected {criterion.expected}",
    )


@_register("json_valid")
def _check_json_valid(response: str, criterion: ScoringCriterion) -> CriterionResult:
    try:
        json.loads(response)
        return CriterionResult(type="json_valid", passed=True, reason="Valid JSON")
    except (json.JSONDecodeError, TypeError) as e:
        return CriterionResult(type="json_valid", passed=False, reason=f"Invalid JSON: {e}")


@_register("json_has_keys")
def _check_json_has_keys(response: str, criterion: ScoringCriterion) -> CriterionResult:
    try:
        data = json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return CriterionResult(
            type="json_has_keys", passed=False, reason="Response is not valid JSON"
        )
    missing = [k for k in criterion.keys if k not in data]
    passed = len(missing) == 0
    reason = "All required keys present" if passed else f"Missing keys: {missing}"
    return CriterionResult(type="json_has_keys", passed=passed, reason=reason)


@_register("regex_match")
def _check_regex_match(response: str, criterion: ScoringCriterion) -> CriterionResult:
    matched = bool(re.search(criterion.pattern, response))
    reason = f"Pattern '{criterion.pattern}' {'matched' if matched else 'not found'}"
    return CriterionResult(type="regex_match", passed=matched, reason=reason)


def score_response(response: str, criteria: list[ScoringCriterion]) -> list[CriterionResult]:
    """Run all criteria checks against a response and return results."""
    results = []
    for criterion in criteria:
        check_fn = _CRITERION_DISPATCH.get(criterion.type)
        if check_fn is None:
            raise ValueError(f"Unknown criterion type: {criterion.type}")
        results.append(check_fn(response, criterion))
    return results


def score_test_case(run_result: dict, test_case: TestCase) -> TestResult:
    """Score a single test case's LLM response against its criteria."""
    response = run_result["llm_response"]
    criteria_results = score_response(response, test_case.criteria)

    passing = sum(1 for cr in criteria_results if cr.passed)
    total = len(criteria_results)
    score = (passing / total) * 100 if total > 0 else 0.0

    logger.info(
        "Test case %s: %.1f%% (%d/%d criteria passed)",
        test_case.id, score, passing, total,
    )

    return TestResult(
        id=test_case.id,
        description=test_case.description,
        passed=score == 100.0,
        score=round(score, 1),
        llm_response=response,
        criteria_results=criteria_results,
    )
