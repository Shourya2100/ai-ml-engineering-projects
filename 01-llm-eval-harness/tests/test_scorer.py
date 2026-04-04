import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.core.scorer import score_response, score_test_case
from app.models.test_case import ScoringCriterion, TestCase


# --- max_length ---

def test_max_length_pass():
    criteria = [ScoringCriterion(type="max_length", value=50)]
    results = score_response("Short text", criteria)
    assert results[0].passed is True


def test_max_length_fail():
    criteria = [ScoringCriterion(type="max_length", value=5)]
    results = score_response("This is way too long", criteria)
    assert results[0].passed is False


# --- min_length ---

def test_min_length_pass():
    criteria = [ScoringCriterion(type="min_length", value=5)]
    results = score_response("This is long enough", criteria)
    assert results[0].passed is True


def test_min_length_fail():
    criteria = [ScoringCriterion(type="min_length", value=100)]
    results = score_response("Too short", criteria)
    assert results[0].passed is False


# --- contains_keywords ---

def test_contains_keywords_pass():
    criteria = [ScoringCriterion(type="contains_keywords", keywords=["hello", "world"])]
    results = score_response("Hello World!", criteria)
    assert results[0].passed is True


def test_contains_keywords_fail():
    criteria = [ScoringCriterion(type="contains_keywords", keywords=["missing"])]
    results = score_response("Nothing here", criteria)
    assert results[0].passed is False


# --- excludes_keywords ---

def test_excludes_keywords_pass():
    criteria = [ScoringCriterion(type="excludes_keywords", keywords=["secret"])]
    results = score_response("Nothing sensitive here", criteria)
    assert results[0].passed is True


def test_excludes_keywords_fail():
    criteria = [ScoringCriterion(type="excludes_keywords", keywords=["sensitive"])]
    results = score_response("This is sensitive data", criteria)
    assert results[0].passed is False


# --- sentence_count ---

def test_sentence_count_pass():
    criteria = [ScoringCriterion(type="sentence_count", expected=2)]
    results = score_response("First sentence. Second sentence.", criteria)
    assert results[0].passed is True


def test_sentence_count_fail():
    criteria = [ScoringCriterion(type="sentence_count", expected=1)]
    results = score_response("One. Two. Three.", criteria)
    assert results[0].passed is False


# --- json_valid ---

def test_json_valid_pass():
    criteria = [ScoringCriterion(type="json_valid")]
    results = score_response('{"name": "test"}', criteria)
    assert results[0].passed is True


def test_json_valid_fail():
    criteria = [ScoringCriterion(type="json_valid")]
    results = score_response("not json at all", criteria)
    assert results[0].passed is False


# --- json_has_keys ---

def test_json_has_keys_pass():
    criteria = [ScoringCriterion(type="json_has_keys", keys=["name", "age"])]
    results = score_response('{"name": "Alice", "age": 30}', criteria)
    assert results[0].passed is True


def test_json_has_keys_fail():
    criteria = [ScoringCriterion(type="json_has_keys", keys=["name", "email"])]
    results = score_response('{"name": "Alice"}', criteria)
    assert results[0].passed is False


# --- regex_match ---

def test_regex_match_pass():
    criteria = [ScoringCriterion(type="regex_match", pattern=r"^\d{3}-\d{4}$")]
    results = score_response("555-1234", criteria)
    assert results[0].passed is True


def test_regex_match_fail():
    criteria = [ScoringCriterion(type="regex_match", pattern=r"^\d{3}-\d{4}$")]
    results = score_response("not a phone number", criteria)
    assert results[0].passed is False


# --- unknown criterion ---

def test_unknown_criterion_raises_value_error():
    criteria = [ScoringCriterion(type="nonexistent_check")]
    with pytest.raises(ValueError, match="Unknown criterion type"):
        score_response("some text", criteria)


# --- score_test_case with mixed results ---

def test_score_test_case_mixed_results():
    test_case = TestCase(
        id="tc_mix",
        description="Mixed results test",
        prompt="Test prompt",
        criteria=[
            ScoringCriterion(type="max_length", value=200),
            ScoringCriterion(type="contains_keywords", keywords=["hello"]),
            ScoringCriterion(type="contains_keywords", keywords=["missing"]),
        ],
    )
    run_result = {"id": "tc_mix", "llm_response": "hello world"}

    result = score_test_case(run_result, test_case)

    assert result.passed is False
    assert result.score == pytest.approx(66.7, abs=0.1)
    assert len(result.criteria_results) == 3
