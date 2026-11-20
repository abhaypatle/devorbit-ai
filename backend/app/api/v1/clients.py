from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import DbSession, get_current_user, require_roles
from app.db.models import Client, User, UserRole
from app.schemas import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])
staff_roles = (UserRole.ADMIN, UserRole.ENGINEER)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(*staff_roles))],
) -> Client:
    client = Client(
        org_id=user.org_id,
        email=payload.email.lower(),
        **payload.model_dump(exclude={"email"}),
    )
    session.add(client)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Client email already exists in this organization") from None
    await session.refresh(client)
    return client


@router.get("", response_model=list[ClientRead])
async def list_clients(
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> list[Client]:
    statement = select(Client).where(Client.org_id == user.org_id)
    if user.role == UserRole.CLIENT:
        statement = statement.where(Client.id == user.client_id)
    return list((await session.scalars(statement.order_by(Client.created_at.desc()))).all())


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> Client:
    return await _get_client(client_id, session, user)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: UUID,
    payload: ClientUpdate,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(*staff_roles))],
) -> Client:
    client = await _get_client(client_id, session, user)
    updates = payload.model_dump(exclude_unset=True)
    if any(field in updates and updates[field] is None for field in ("name", "email")):
        raise HTTPException(status_code=422, detail="Client name and email cannot be null")
    for field, value in updates.items():
        setattr(client, field, value.lower() if field == "email" and value else value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Client email already exists in this organization") from None
    await session.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    client = await _get_client(client_id, session, user)
    await session.delete(client)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Client has project orders and cannot be deleted") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _get_client(client_id: UUID, session: DbSession, user: User) -> Client:
    statement = select(Client).where(Client.id == client_id, Client.org_id == user.org_id)
    if user.role == UserRole.CLIENT:
        statement = statement.where(Client.id == user.client_id)
    client = await session.scalar(statement)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
