from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DbSession, get_current_user, require_roles
from app.db.models import ProjectOrder, Subscription, User, UserRole
from app.schemas import SubscriptionCreate, SubscriptionRead, SubscriptionUpdate

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
staff_roles = (UserRole.ADMIN, UserRole.ENGINEER)


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(*staff_roles))],
) -> Subscription:
    project = await session.scalar(
        select(ProjectOrder).where(
            ProjectOrder.id == payload.project_id,
            ProjectOrder.org_id == user.org_id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project order not found")
    subscription_data = payload.model_dump()
    if subscription_data["next_billing_date"] is None:
        subscription_data["next_billing_date"] = date.today()
    subscription = Subscription(org_id=user.org_id, **subscription_data)
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


@router.get("", response_model=list[SubscriptionRead])
async def list_subscriptions(
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> list[Subscription]:
    statement = select(Subscription).where(Subscription.org_id == user.org_id)
    if user.role == UserRole.CLIENT:
        statement = statement.join(ProjectOrder).where(ProjectOrder.client_id == user.client_id)
    return list((await session.scalars(statement.order_by(Subscription.created_at.desc()))).all())


@router.get("/{subscription_id}", response_model=SubscriptionRead)
async def get_subscription(
    subscription_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> Subscription:
    return await _get_subscription(subscription_id, session, user)


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: UUID,
    payload: SubscriptionUpdate,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(*staff_roles))],
) -> Subscription:
    subscription = await _get_subscription(subscription_id, session, user)
    updates = payload.model_dump(exclude_unset=True)
    required_fields = ("name", "amount", "currency", "interval", "status")
    if any(field in updates and updates[field] is None for field in required_fields):
        raise HTTPException(status_code=422, detail="Required subscription fields cannot be null")
    for field, value in updates.items():
        setattr(subscription, field, value)
    await session.commit()
    await session.refresh(subscription)
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    subscription = await _get_subscription(subscription_id, session, user)
    await session.delete(subscription)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _get_subscription(
    subscription_id: UUID,
    session: AsyncSession,
    user: User,
) -> Subscription:
    statement = select(Subscription).where(
        Subscription.id == subscription_id,
        Subscription.org_id == user.org_id,
    )
    if user.role == UserRole.CLIENT:
        statement = statement.join(ProjectOrder).where(ProjectOrder.client_id == user.client_id)
    subscription = await session.scalar(statement)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription
