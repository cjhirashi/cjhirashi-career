"""
Rutas de gestión de documentos: CRUD completo.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse
)
from models.document import Document
from models.user import User
from middleware.auth import get_current_user
from database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los documentos del usuario actual con paginación.

    Args:
        skip: Número de documentos a saltar
        limit: Número máximo de documentos a retornar
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de documentos con total
    """
    # Obtener total de documentos
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )
    total = count_result.scalar()

    # Obtener documentos con paginación
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse.model_validate(doc) for doc in documents]
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un documento específico por ID.

    Args:
        document_id: ID del documento
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Documento solicitado

    Raises:
        HTTPException 404: Si el documento no existe o no pertenece al usuario
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )

    return DocumentResponse.model_validate(document)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo documento para el usuario actual.

    Args:
        document_data: Datos del documento a crear
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Documento creado
    """
    # Crear nuevo documento
    new_document = Document(
        user_id=current_user.id,
        type=document_data.type,
        title=document_data.title,
        data=document_data.data
    )

    db.add(new_document)
    await db.flush()
    await db.refresh(new_document)

    logger.info(f"Document created: id={new_document.id}, type={new_document.type}, user={current_user.username}")

    return DocumentResponse.model_validate(new_document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un documento existente.

    Args:
        document_id: ID del documento a actualizar
        document_data: Nuevos datos del documento
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Documento actualizado

    Raises:
        HTTPException 404: Si el documento no existe o no pertenece al usuario
    """
    # Buscar documento
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )

    # Actualizar campos si se proporcionan
    if document_data.type is not None:
        document.type = document_data.type
    if document_data.title is not None:
        document.title = document_data.title
    if document_data.data is not None:
        document.data = document_data.data

    await db.flush()
    await db.refresh(document)

    logger.info(f"Document updated: id={document.id}, user={current_user.username}")

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un documento existente.

    Args:
        document_id: ID del documento a eliminar
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Raises:
        HTTPException 404: Si el documento no existe o no pertenece al usuario
    """
    # Buscar documento
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )

    await db.delete(document)
    logger.info(f"Document deleted: id={document_id}, user={current_user.username}")


@router.get("/type/{doc_type}", response_model=DocumentListResponse)
async def list_documents_by_type(
    doc_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista documentos del usuario actual filtrados por tipo.

    Args:
        doc_type: Tipo de documento (ej: 'cv', 'cover_letter')
        skip: Número de documentos a saltar
        limit: Número máximo de documentos a retornar
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de documentos del tipo especificado
    """
    # Obtener total de documentos del tipo
    count_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.user_id == current_user.id,
            Document.type == doc_type
        )
    )
    total = count_result.scalar()

    # Obtener documentos con paginación
    result = await db.execute(
        select(Document)
        .where(
            Document.user_id == current_user.id,
            Document.type == doc_type
        )
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse.model_validate(doc) for doc in documents]
    )
