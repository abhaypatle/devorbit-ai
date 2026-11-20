from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import BillingInterval, OrderStatus, SubscriptionStatus, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    organization_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")
    full_name: str = Field(min_length=1, max_length=160)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    organization_slug: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole
    client_id: UUID | None = None


class UserRead(ORMModel):
    id: UUID
    org_id: UUID
    client_id: UUID | None
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: EmailStr
    company: str | None = Field(default=None, max_length=160)
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    company: str | None = Field(default=None, max_length=160)
    notes: str | None = None


class ClientRead(ORMModel):
    id: UUID
    org_id: UUID
    name: str
    email: EmailStr
    company: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class OrderCreate(BaseModel):
    client_id: UUID
    project_key: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: OrderStatus = OrderStatus.DRAFT
    budget: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")


class OrderUpdate(BaseModel):
    client_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: OrderStatus | None = None
    budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


class OrderRead(ORMModel):
    id: UUID
    org_id: UUID
    client_id: UUID
    project_key: str
    name: str
    description: str | None
    status: OrderStatus
    budget: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class SubscriptionCreate(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=160)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    interval: BillingInterval
    next_billing_date: date | None = None


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    interval: BillingInterval | None = None
    next_billing_date: date | None = None
    status: SubscriptionStatus | None = None


class SubscriptionRead(ORMModel):
    id: UUID
    org_id: UUID
    project_id: UUID
    name: str
    amount: Decimal
    currency: str
    interval: BillingInterval
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime
