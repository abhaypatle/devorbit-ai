from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import DbSession, get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Organization, User, UserRole
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: DbSession) -> TokenResponse:
    organization = Organization(name=payload.organization_name, slug=payload.organization_slug)
    user = User(
        organization=organization,
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=UserRole.ADMIN,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug or account already exists",
        ) from None
    await session.refresh(user)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: DbSession) -> TokenResponse:
    user = await session.scalar(
        select(User)
        .join(Organization)
        .where(
            User.email == payload.email.lower(),
            Organization.slug == payload.organization_slug,
            User.is_active.is_(True),
        )
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _token_response(user)


@router.get("/me", response_model=UserRead)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: DbSession,
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> User:
    if payload.role == UserRole.CLIENT and payload.client_id is None:
        raise HTTPException(status_code=422, detail="Client users must be linked to a client")
    if payload.role != UserRole.CLIENT and payload.client_id is not None:
        raise HTTPException(status_code=422, detail="Only client users can be linked to a client")
    if payload.client_id is not None:
        from app.db.models import Client

        client = await session.scalar(
            select(Client).where(Client.id == payload.client_id, Client.org_id == admin.org_id)
        )
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")
    user = User(
        org_id=admin.org_id,
        client_id=payload.client_id,
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Account already exists in this organization") from None
    await session.refresh(user)
    return user


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id=user.id, org_id=user.org_id, role=user.role.value),
        user=UserRead.model_validate(user),
    )
