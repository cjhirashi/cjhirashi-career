"""Validación del tablero de tareas y del scheduler autónomo (ADR-015)."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from models.bedrock_task import BedrockTask
from schemas.bedrock_task import BedrockTaskCreate, BedrockTaskUpdate
from services import task_scheduler
from services.admin_sections import list_section_specs, match_section
from services.bedrock.agent_profiles import AGENT_VACANCY_SEARCH
from services.bedrock.errors import BedrockError


def test_tasks_section_is_top_level():
    spec = next(s for s in list_section_specs() if s.id == "agent-tasks")
    assert spec.path == "/tasks"
    assert spec.resource_key == "agent-tasks"
    assert spec.group == "Principal"
    view_keys = {v.key for v in spec.views}
    assert view_keys >= {"list", "calendar", "kanban", "gantt", "view", "edit"}
    matched = match_section("/tasks")
    assert matched is not None
    assert matched[0].id == "agent-tasks"


def test_create_user_task_clears_agent_profile():
    payload = BedrockTaskCreate(
        title="Revisar CV",
        assignee_type="user",
        agent_profile_id=AGENT_VACANCY_SEARCH,
    )
    assert payload.agent_profile_id is None
    assert payload.assignee_type == "user"


def test_create_agent_task_requires_profile():
    with pytest.raises(ValidationError):
        BedrockTaskCreate(title="Buscar vacantes", assignee_type="agent")


def test_create_agent_task_rejects_unknown_profile():
    with pytest.raises(ValidationError):
        BedrockTaskCreate(
            title="X",
            assignee_type="agent",
            agent_profile_id="agent_does_not_exist",
        )


def test_create_agent_task_accepts_catalog_profile():
    payload = BedrockTaskCreate(
        title="Buscar vacantes",
        assignee_type="agent",
        agent_profile_id=AGENT_VACANCY_SEARCH,
        scheduled_at=datetime(2026, 8, 27, 15, 0, tzinfo=timezone.utc),
    )
    assert payload.agent_profile_id == AGENT_VACANCY_SEARCH


def test_due_at_cannot_precede_scheduled_at():
    start = datetime(2026, 8, 27, 15, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        BedrockTaskCreate(
            title="X",
            scheduled_at=start,
            due_at=start - timedelta(hours=1),
        )


def test_partial_update_status_does_not_require_assignee():
    payload = BedrockTaskUpdate(status="done")
    assert payload.status == "done"
    assert payload.assignee_type is None


def test_build_execution_prompt_includes_title():
    task = BedrockTask(
        id="btk-1",
        user_id="usr-1",
        title="Publicar en LinkedIn",
        description="Texto del post",
        status="pending",
        assignee_type="agent",
        agent_profile_id="agent_linkedin_publishing",
        priority="high",
    )
    prompt = task_scheduler.build_execution_prompt(task)
    assert "Publicar en LinkedIn" in prompt
    assert "btk-1" in prompt
    assert "no está en sesión" in prompt


def _execute_result(task: BedrockTask | None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = task
    return result


@pytest.mark.asyncio
async def test_claim_task_for_user_only_runnable_agents():
    user_task = BedrockTask(
        id="btk-user",
        user_id="usr-1",
        title="Manual",
        status="pending",
        assignee_type="user",
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_execute_result(user_task))
    assert await task_scheduler.claim_task_for_user(db, "usr-1", "btk-user") is None

    agent_task = BedrockTask(
        id="btk-agent",
        user_id="usr-1",
        title="Agente",
        status="pending",
        assignee_type="agent",
        agent_profile_id=AGENT_VACANCY_SEARCH,
    )
    db.execute = AsyncMock(return_value=_execute_result(agent_task))
    claimed = await task_scheduler.claim_task_for_user(db, "usr-1", "btk-agent")
    assert claimed is not None
    assert claimed.status == "in_progress"
    db.flush.assert_awaited()


@pytest.mark.asyncio
async def test_claim_due_task_ids_skips_future_and_user_tasks(monkeypatch):
    now = datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc)
    due = BedrockTask(
        id="btk-due",
        user_id="usr-1",
        title="Vencida",
        status="pending",
        assignee_type="agent",
        agent_profile_id=AGENT_VACANCY_SEARCH,
        scheduled_at=now - timedelta(minutes=5),
    )
    scalars = MagicMock()
    scalars.all.return_value = [due]
    result = MagicMock()
    result.scalars.return_value = scalars
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    class _SessionCM:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(task_scheduler, "AsyncSessionLocal", lambda: _SessionCM())
    ids = await task_scheduler.claim_due_task_ids(now)
    assert ids == ["btk-due"]
    assert due.status == "in_progress"


@pytest.mark.asyncio
async def test_execute_claimed_task_marks_done(monkeypatch):
    task = BedrockTask(
        id="btk-run",
        user_id="usr-1",
        title="Buscar",
        status="in_progress",
        assignee_type="agent",
        agent_profile_id=AGENT_VACANCY_SEARCH,
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_execute_result(task))
    db.refresh = AsyncMock()
    db.commit = AsyncMock()

    class _SessionCM:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(task_scheduler, "AsyncSessionLocal", lambda: _SessionCM())
    monkeypatch.setattr(
        "services.bedrock.agent_loop.run_single_turn_sync",
        AsyncMock(return_value={"type": "done", "reply": "Guardé L1"}),
    )

    await task_scheduler.execute_claimed_task("btk-run")
    assert task.status == "done"
    assert task.execution_result == "Guardé L1"
    assert task.executed_at is not None
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_execute_claimed_task_marks_failed_on_bedrock_error(monkeypatch):
    task = BedrockTask(
        id="btk-fail",
        user_id="usr-1",
        title="Buscar",
        status="in_progress",
        assignee_type="agent",
        agent_profile_id=AGENT_VACANCY_SEARCH,
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_execute_result(task))
    db.rollback = AsyncMock()
    db.commit = AsyncMock()
    db.get = AsyncMock(return_value=task)

    class _SessionCM:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(task_scheduler, "AsyncSessionLocal", lambda: _SessionCM())

    async def _boom(*_args, **_kwargs):
        raise BedrockError("presupuesto agotado")

    with patch("services.bedrock.agent_loop.run_single_turn_sync", _boom):
        await task_scheduler.execute_claimed_task("btk-fail")

    assert task.status == "failed"
    assert "presupuesto" in (task.error_message or "")
