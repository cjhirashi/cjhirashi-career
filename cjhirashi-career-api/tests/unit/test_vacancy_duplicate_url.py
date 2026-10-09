"""Duplicate vacancy_url must surface as 409, not 500 (checklist Paulina #4).

`Vacancy.vacancy_url` has a DB-level UNIQUE constraint (vacancy.py). Creating
a second row with the same URL raises `sqlalchemy.exc.IntegrityError` at
flush time. The generic CRUD route (career_common.py) now catches that,
rolls back, and returns HTTP 409 instead of an unhandled 500 — this test
pins the repository-level precondition that fix depends on.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.vacancy import Vacancy
from repositories.career_repository import CareerRepository


@pytest.mark.asyncio
async def test_duplicate_vacancy_url_raises_integrity_error(
    db_session: AsyncSession, test_user: User
):
    repo = CareerRepository(Vacancy, resource_key="vacancies")
    payload = {
        "exact_role": "Backend Engineer",
        "vacancy_url": "https://example.com/jobs/duplicate-url-test",
        "company": "Acme",
    }
    await repo.create_for_user(db_session, test_user.id, dict(payload))

    with pytest.raises(IntegrityError):
        await repo.create_for_user(db_session, test_user.id, dict(payload))

    # The route's except-clause rolls back before returning 409; do the same
    # here so the session stays usable for any later assertion/fixture teardown.
    await db_session.rollback()
