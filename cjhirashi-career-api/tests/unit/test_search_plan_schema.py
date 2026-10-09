"""SearchPlanResponse must accept NULL completion_percentage (checklist Paulina #2).

The model column is nullable (search_plan.py), but the response schema required
a non-optional int, so any row with completion_percentage=NULL raised a
validation error and GET /career/search-plans returned 500.
"""
from datetime import datetime, timezone

from schemas.career_search import SearchPlanResponse


def _payload(**overrides):
    base = dict(
        id="spl-1",
        user_id="usr-2",
        plan_status="not_started",
        completion_percentage=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return base


def test_response_accepts_null_completion_percentage():
    row = SearchPlanResponse.model_validate(_payload(completion_percentage=None))
    assert row.completion_percentage is None


def test_response_accepts_int_completion_percentage():
    row = SearchPlanResponse.model_validate(_payload(completion_percentage=42))
    assert row.completion_percentage == 42
