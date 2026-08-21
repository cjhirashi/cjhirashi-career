"""
Generic CRUD router factory for the career-domain (v2) tables.

Builds a standard `GET list / GET by id / POST / PUT / DELETE` APIRouter
for a given (model, schemas) tuple. Every endpoint requires JWT
authentication and enforces row-level user isolation via
`repositories.career_repository.CareerRepository` - the `user_id` is
always taken from the authenticated user, never from the request body or
query string.
"""
from typing import Dict, List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base, get_db
from middleware.auth import get_current_user
from models.user import User
from repositories.career_repository import CareerRepository

# resource_key -> SQLAlchemy model, populated automatically below as each
# `build_crud_router(...)` call registers itself - never maintained by hand.
# This is what lets Agent Bedrock's tools (services/bedrock_service.py)
# operate any of the ~30 career-domain resources generically, the same way
# CareerResourceView.tsx's CAREER_RESOURCES does on the frontend.
RESOURCE_REGISTRY: Dict[str, Type[Base]] = {}


def build_crud_router(
    *,
    prefix: str,
    tags: List[str],
    model: Type[Base],
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    response_schema: Type[BaseModel],
    entity_name: str,
    vectorize: bool = True,
) -> APIRouter:
    """Create an APIRouter with standard CRUD endpoints for `model`.

    `vectorize=False` opts this resource out of the Qdrant knowledge-base
    indexing that otherwise happens automatically on every write (see
    `CareerRepository._index_for_search`) - use it for PDF-content tables
    (e.g. `cv-versions`): the agent should read those straight from
    Postgres, never from a copy in the vector store.
    """
    router = APIRouter(prefix=prefix, tags=tags)
    resource_key = prefix.lstrip("/")
    repository: CareerRepository = CareerRepository(model, resource_key=resource_key, vectorize=vectorize)
    RESOURCE_REGISTRY[resource_key] = model

    class CountResponse(BaseModel):
        count: int

    @router.get("", response_model=List[response_schema], summary=f"List {entity_name}")
    async def list_items(
        skip: int = Query(0, ge=0, description="Pagination offset"),
        limit: int = Query(20, ge=1, le=100, description="Page size"),
        sort_by: Optional[str] = Query(None, description="Column name to sort by"),
        sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
        search: Optional[str] = Query(None, description="Case-insensitive search across text columns"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await repository.list_for_user(
            db, current_user.id, skip=skip, limit=limit, sort_by=sort_by, sort_dir=sort_dir, search=search
        )

    # Declared before "/{item_id}" - a path-param route would otherwise catch
    # "/count" as if item_id="count".
    @router.get("/count", response_model=CountResponse, summary=f"Count {entity_name}")
    async def count_items(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        count = await repository.count_for_user(db, current_user.id)
        return CountResponse(count=count)

    @router.get(
        "/{item_id}", response_model=response_schema, summary=f"Get a single {entity_name}"
    )
    async def get_item(
        item_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        obj = await repository.get_for_user(db, current_user.id, item_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found"
            )
        return obj

    @router.post(
        "",
        response_model=response_schema,
        status_code=status.HTTP_201_CREATED,
        summary=f"Create a {entity_name}",
    )
    async def create_item(
        payload: create_schema,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        obj = await repository.create_for_user(db, current_user.id, payload.model_dump())
        return obj

    @router.put(
        "/{item_id}", response_model=response_schema, summary=f"Update a {entity_name}"
    )
    async def update_item(
        item_id: int,
        payload: update_schema,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        data = payload.model_dump(exclude_unset=True)
        obj = await repository.update_for_user(db, current_user.id, item_id, data)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found"
            )
        return obj

    @router.delete(
        "/{item_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Delete a {entity_name}",
    )
    async def delete_item(
        item_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        deleted = await repository.delete_for_user(db, current_user.id, item_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found"
            )

    return router
