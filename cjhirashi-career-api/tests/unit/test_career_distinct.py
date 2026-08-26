"""Distinct column values for creatable selects."""
from models.work_history import WorkHistory
from repositories.career_repository import CareerRepository


def test_as_bool_accepts_spanish_and_english():
    assert CareerRepository._as_bool("true") is True
    assert CareerRepository._as_bool("sí") is True
    assert CareerRepository._as_bool("false") is False
    assert CareerRepository._as_bool("no") is False
    assert CareerRepository._as_bool("maybe") is None


def test_as_bool_maps_each_multi_select_value():
    parsed = [CareerRepository._as_bool(item) for item in ["true", "false"]]
    assert parsed == [True, False]


def test_contract_type_is_a_distinct_text_field():
    repo = CareerRepository(WorkHistory, resource_key="work-history", vectorize=False)
    assert repo.is_distinct_field("contract_type") is True
    assert repo.is_distinct_field("industry_sector") is True
    assert repo.is_distinct_field("id") is False
    assert repo.is_distinct_field("user_id") is False
    assert repo.is_distinct_field("not_a_column") is False
