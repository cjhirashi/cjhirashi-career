"""
Repositorio de `bedrock_tasks`: tablero de tareas (usuario o agente) con subtareas de un nivel.

Traslado de la parte de tareas de `CareerRepository` (API): listado con búsqueda, filtros,
orden y paginación, `count`, valores distintos, validación de `parent_id` y sincronización de
`subtasks` (ADR-016). Aislamiento por `user_id` en cada consulta; `user_id` nunca se toma del
payload. Las subtareas se validan con `SubtaskInput` (Pydantic) y se aplica `model_dump()`, como la API;
la validación del resto de campos queda en la capa de rutas.
"""
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import Boolean as SABoolean
from sqlalchemy import String, Text, func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_task import BedrockTask
from schemas.bedrock_task import SubtaskInput

_COLUMNS = list(inspect(BedrockTask).mapper.column_attrs)
_COLUMN_NAMES = {attr.key for attr in _COLUMNS}
_TEXT_COLUMNS = [attr.key for attr in _COLUMNS if isinstance(attr.columns[0].type, (String, Text))]
_RESERVED = frozenset({"id", "user_id"})
_DISTINCT_LIMIT = 500


def _apply_search(stmt, search: Optional[str]):
    if search and _TEXT_COLUMNS:
        like = f"%{search}%"
        stmt = stmt.where(or_(*(getattr(BedrockTask, col).ilike(like) for col in _TEXT_COLUMNS)))
    return stmt


def _as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes", "si", "sí"):
            return True
        if lowered in ("false", "0", "no"):
            return False
    return None


def _apply_filters(stmt, filters: Optional[dict]):
    """AND de igualdad / pertenencia. Las claves desconocidas, `id` y `user_id` se ignoran."""
    if not filters:
        return stmt
    for field, raw in filters.items():
        if field not in _COLUMN_NAMES or field in _RESERVED:
            continue
        column = getattr(BedrockTask, field)
        values = raw if isinstance(raw, list) else [raw]
        values = [item for item in values if item is not None and item != ""]
        if not values:
            continue
        if isinstance(column.type, SABoolean):
            wanted = [b for b in (_as_bool(item) for item in values) if b is not None]
            if not wanted:
                continue
            stmt = stmt.where(column.in_(wanted) if len(wanted) > 1 else column.is_(wanted[0]))
        elif len(values) == 1:
            stmt = stmt.where(column == values[0])
        else:
            stmt = stmt.where(column.in_([str(item) for item in values]))
    return stmt


async def list_for_user(
    db: AsyncSession,
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    sort_by: Optional[str] = None,
    sort_dir: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Sequence[BedrockTask]:
    """Página de tareas del usuario. `sort_by` inválido o ausente = más recientes primero (`id desc`)."""
    stmt = select(BedrockTask).where(BedrockTask.user_id == user_id)
    stmt = _apply_filters(_apply_search(stmt, search), filters)
    if sort_by and sort_by in _COLUMN_NAMES:
        column = getattr(BedrockTask, sort_by)
        stmt = stmt.order_by(column.desc() if sort_dir == "desc" else column.asc())
    else:
        stmt = stmt.order_by(BedrockTask.id.desc())
    result = await db.execute(stmt.offset(skip).limit(limit))
    return result.scalars().all()


async def count_for_user(
    db: AsyncSession, user_id: str, search: Optional[str] = None, filters: Optional[dict] = None
) -> int:
    stmt = select(func.count()).select_from(BedrockTask).where(BedrockTask.user_id == user_id)
    stmt = _apply_filters(_apply_search(stmt, search), filters)
    return (await db.execute(stmt)).scalar_one()


def is_distinct_field(field: str) -> bool:
    """True si `field` es una columna de texto que puede respaldar un select creable."""
    return field in _TEXT_COLUMNS and field not in _RESERVED


async def distinct_values_for_user(db: AsyncSession, user_id: str, field: str) -> List[str]:
    if not is_distinct_field(field):
        raise ValueError(f"Field {field!r} is not a text column on this resource")
    column = getattr(BedrockTask, field)
    stmt = (
        select(column)
        .where(BedrockTask.user_id == user_id, column.is_not(None), column != "")
        .distinct()
        .order_by(column.asc())
        .limit(_DISTINCT_LIMIT)
    )
    values: List[str] = []
    seen: set = set()
    for raw in (await db.execute(stmt)).scalars().all():
        text = str(raw).strip()
        if text and text not in seen:
            seen.add(text)
            values.append(text)
    return values


async def get_for_user(db: AsyncSession, user_id: str, item_id: str) -> Optional[BedrockTask]:
    result = await db.execute(
        select(BedrockTask).where(BedrockTask.id == item_id, BedrockTask.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_children(db: AsyncSession, user_id: str, parent_id: str) -> List[BedrockTask]:
    result = await db.execute(
        select(BedrockTask)
        .where(BedrockTask.user_id == user_id, BedrockTask.parent_id == parent_id)
        .order_by(BedrockTask.sort_order.asc(), BedrockTask.id.asc())
    )
    return list(result.scalars().all())


async def _validate_parent(
    db: AsyncSession, user_id: str, parent_id: Optional[str], self_id: Optional[str] = None
) -> None:
    if not parent_id:
        return
    if self_id and parent_id == self_id:
        raise ValueError("una tarea no puede ser padre de sí misma")
    parent = await db.get(BedrockTask, parent_id)
    if parent is None or parent.user_id != user_id:
        raise ValueError("parent_id no existe o no es tuyo")
    if parent.parent_id:
        raise ValueError("las subtareas no pueden tener subtareas")


async def _sync_subtasks(db: AsyncSession, user_id: str, parent: BedrockTask, items: Sequence[dict]) -> None:
    if parent.parent_id:
        raise ValueError("las subtareas no pueden tener subtareas")
    existing = {child.id: child for child in await list_children(db, user_id, parent.id)}
    keep: set = set()
    for index, raw in enumerate(items):
        payload = raw if isinstance(raw, dict) else raw.model_dump()
        payload = {**payload, "parent_id": parent.id, "sort_order": index}
        parsed = SubtaskInput.model_validate(payload)
        data = parsed.model_dump(exclude={"id"})
        data["parent_id"] = parent.id
        data["sort_order"] = index
        child_id = parsed.id
        if child_id and child_id in existing:
            child = existing[child_id]
            for key, value in data.items():
                setattr(child, key, value)
            keep.add(child_id)
        else:
            child = BedrockTask(user_id=user_id, **data)
            db.add(child)
            await db.flush()
            keep.add(child.id)
    for child_id, child in existing.items():
        if child_id not in keep:
            await db.delete(child)


async def create_for_user(db: AsyncSession, user_id: str, data: Dict[str, Any]) -> BedrockTask:
    """Crea la tarea (y sus `subtasks` anidadas); `user_id` se fuerza, nunca viene del payload."""
    data = dict(data)
    data.pop("user_id", None)
    subtasks = data.pop("subtasks", None)
    await _validate_parent(db, user_id, data.get("parent_id"))
    obj = BedrockTask(user_id=user_id, **data)
    db.add(obj)
    await db.flush()
    if subtasks is not None:
        await _sync_subtasks(db, user_id, obj, subtasks)
    await db.commit()
    return obj


async def update_for_user(
    db: AsyncSession, user_id: str, item_id: str, data: Dict[str, Any]
) -> Optional[BedrockTask]:
    """Actualización parcial acotada al usuario. `None` si no existe o no es suya.

    `subtasks` ausente no toca las hijas; una lista las sincroniza (`[]` las borra todas).
    """
    obj = await get_for_user(db, user_id, item_id)
    if obj is None:
        return None
    data = dict(data)
    data.pop("user_id", None)
    subtasks = data.pop("subtasks", None)
    if "parent_id" in data:
        await _validate_parent(db, user_id, data.get("parent_id"), item_id)
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    if subtasks is not None:
        await _sync_subtasks(db, user_id, obj, subtasks)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_for_user(db: AsyncSession, user_id: str, item_id: str) -> bool:
    """Borra la tarea; las hijas caen por `ON DELETE CASCADE` de `parent_id`."""
    obj = await get_for_user(db, user_id, item_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.commit()
    return True
