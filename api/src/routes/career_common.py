"""
Generic CRUD router factory for the career-domain (v2) tables.

Builds a standard `GET list / GET by id / POST / PUT / DELETE` APIRouter
for a given (model, schemas) tuple. Every endpoint requires JWT
authentication and enforces row-level user isolation via
`repositories.career_repository.CareerRepository` - the `user_id` is
always taken from the authenticated user, never from the request body or
query string.
"""
from typing import List, Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base, get_db
from middleware.auth import get_current_user
from models.user import User
from repositories.career_repository import CareerRepository


def build_crud_router(
    *,
    prefix: str,
    tags: List[str],
    model: Type[Base],
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    response_schema: Type[BaseModel],
    entity_name: str,
) -> APIRouter:
    """Create an APIRouter with standard CRUD endpoints for `model`."""
    router = APIRouter(prefix=prefix, tags=tags)
    repository: CareerRepository = CareerRepository(model)

    @router.get("", response_model=List[response_schema], summary=f"List {entity_name}")
    async def list_items(
        skip: int = Query(0, ge=0, description="Pagination offset"),
        limit: int = Query(20, ge=1, le=100, description="Page size"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await repository.list_for_user(db, current_user.id, skip=skip, limit=limit)

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
