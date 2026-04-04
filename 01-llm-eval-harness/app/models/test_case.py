from pydantic import BaseModel


class ScoringCriterion(BaseModel):
    type: str
    value: int | None = None
    keywords: list[str] | None = None
    expected: int | None = None
    pattern: str | None = None
    keys: list[str] | None = None


class TestCase(BaseModel):
    id: str
    description: str
    prompt: str
    input: str | None = None
    criteria: list[ScoringCriterion]


class TestSuite(BaseModel):
    suite_name: str
    model: str
    max_tokens: int = 500
    temperature: float = 0.0
    test_cases: list[TestCase]
