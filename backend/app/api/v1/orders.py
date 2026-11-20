from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import DbSession, get_current_user, require_roles
from app.db.models import Client, ProjectOrder, User, UserRole
from app.schemas import OrderCreate, OrderRead, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])
staff_roles = (UserRole.ADMIN, UserRole.ENGINEER)


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(*staff_roles))],
) -> ProjectOrder:
    client = await session.scalar(
        select(Client).where(Client.id == payload.client_id, Client.org_id == user.org_id)
    )
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    order = ProjectOrder(org_id=user.org_id, **payload.model_dump())
    session.add(order)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Project key already exists in this organization") from None
    await session.refresh(order)
    return order


@router.get("", response_model=list[OrderRead])
async def list_orders(
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> list[ProjectOrder]:
    statement = select(ProjectOrder).where(ProjectOrder.org_id == user.org_id)
    if user.role == UserRole.CLIENT:
        statement = statement.where(ProjectOrder.client_id == user.client_id)
    return list((await session.scalars(statement.order_by(ProjectOrder.created_at.desc()))).all())


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> ProjectOrder:
    return await _get_order(order_id, session, user)


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: UUID,
    payload: OrderUpdate,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(*staff_roles))],
) -> ProjectOrder:
    order = await _get_order(order_id, session, user)
    updates = payload.model_dump(exclude_unset=True)
    required_fields = ("client_id", "name", "status", "budget", "currency")
    if any(field in updates and updates[field] is None for field in required_fields):
        raise HTTPException(status_code=422, detail="Required project order fields cannot be null")
    if "client_id" in updates:
        client = await session.scalar(
            select(Client).where(Client.id == updates["client_id"], Client.org_id == user.org_id)
        )
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")
    for field, value in updates.items():
        setattr(order, field, value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Project key or ownership conflicts with an existing record") from None
    await session.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    order = await _get_order(order_id, session, user)
    await session.delete(order)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _get_order(order_id: UUID, session: DbSession, user: User) -> ProjectOrder:
    statement = select(ProjectOrder).where(
        ProjectOrder.id == order_id,
        ProjectOrder.org_id == user.org_id,
    )
    if user.role == UserRole.CLIENT:
        statement = statement.where(ProjectOrder.client_id == user.client_id)
    order = await session.scalar(statement)
    if order is None:
        raise HTTPException(status_code=404, detail="Project order not found")
    return order
