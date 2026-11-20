import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import Client, Organization, ProjectOrder, Subscription, BillingInterval


async def register(
    client: AsyncClient,
    *,
    organization_name: str,
    organization_slug: str,
    email: str,
) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": organization_name,
            "organization_slug": organization_slug,
            "full_name": "Workspace Admin",
            "email": email,
            "password": "secure-test-password-123",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["user"]["org_id"]


async def test_tenant_isolation_and_crud(client: AsyncClient) -> None:
    token_a, _ = await register(
        client,
        organization_name="Agency A",
        organization_slug="agency-a",
        email="admin@agency-a.example.com",
    )
    token_b, _ = await register(
        client,
        organization_name="Agency B",
        organization_slug="agency-b",
        email="admin@agency-b.example.com",
    )

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    client_response = await client.post(
        "/api/v1/clients",
        headers=headers_a,
        json={"name": "Acme", "email": "ops@acme.example.com", "company": "Acme Inc"},
    )
    assert client_response.status_code == 201, client_response.text
    client_id = client_response.json()["id"]

    order_response = await client.post(
        "/api/v1/orders",
        headers=headers_a,
        json={
            "client_id": client_id,
            "project_key": "ACME-1",
            "name": "Acme platform",
            "budget": "12000.00",
        },
    )
    assert order_response.status_code == 201, order_response.text
    order_id = order_response.json()["id"]

    subscription_response = await client.post(
        "/api/v1/subscriptions",
        headers=headers_a,
        json={
            "project_id": order_id,
            "name": "AI support",
            "amount": "500.00",
            "interval": "monthly",
        },
    )
    assert subscription_response.status_code == 201, subscription_response.text
    assert (await client.get("/api/v1/clients", headers=headers_b)).json() == []
    assert (await client.get(f"/api/v1/clients/{client_id}", headers=headers_b)).status_code == 404
    assert (await client.get("/api/v1/orders", headers=headers_b)).json() == []
    assert (await client.get(f"/api/v1/orders/{order_id}", headers=headers_b)).status_code == 404
    assert (await client.get("/api/v1/subscriptions", headers=headers_b)).json() == []
    cross_tenant_order = await client.post(
        "/api/v1/orders",
        headers=headers_b,
        json={"client_id": client_id, "project_key": "BAD-1", "name": "Cross-tenant"},
    )
    assert cross_tenant_order.status_code == 404
    assert (await client.delete(f"/api/v1/clients/{client_id}", headers=headers_a)).status_code == 409
    assert (await client.delete(f"/api/v1/orders/{order_id}", headers=headers_a)).status_code == 204
    assert (await client.get("/api/v1/subscriptions", headers=headers_a)).json() == []


async def test_client_role_is_limited_to_own_project(client: AsyncClient) -> None:
    admin_token, _ = await register(
        client,
        organization_name="Client Portal Org",
        organization_slug="client-portal-org",
        email="admin@portal.example.com",
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client_record = await client.post(
        "/api/v1/clients",
        headers=admin_headers,
        json={"name": "Client One", "email": "client@one.example.com"},
    )
    client_id = client_record.json()["id"]
    order = await client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={"client_id": client_id, "project_key": "ONE-1", "name": "Project One"},
    )
    subscription = await client.post(
        "/api/v1/subscriptions",
        headers=admin_headers,
        json={
            "project_id": order.json()["id"],
            "name": "Support",
            "amount": "125.00",
            "interval": "monthly",
        },
    )
    assert subscription.status_code == 201
    await client.post(
        "/api/v1/auth/users",
        headers=admin_headers,
        json={
            "full_name": "Client User",
            "email": "portal@one.example.com",
            "password": "secure-client-password-123",
            "role": "client",
            "client_id": client_id,
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "organization_slug": "client-portal-org",
            "email": "portal@one.example.com",
            "password": "secure-client-password-123",
        },
    )
    assert login.status_code == 200, login.text
    client_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert [row["id"] for row in (await client.get("/api/v1/orders", headers=client_headers)).json()] == [
        order.json()["id"]
    ]
    assert [row["id"] for row in (await client.get(
        "/api/v1/subscriptions", headers=client_headers
    )).json()] == [subscription.json()["id"]]
    assert (await client.post(
        "/api/v1/clients",
        headers=client_headers,
        json={"name": "Not allowed", "email": "bad@one.example.com"},
    )).status_code == 403


async def test_authentication_and_organization_collision(client: AsyncClient) -> None:
    await register(
        client,
        organization_name="First",
        organization_slug="same-slug",
        email="same@example.com",
    )
    duplicate = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Second",
            "organization_slug": "same-slug",
            "full_name": "Other Admin",
            "email": "other@example.com",
            "password": "secure-test-password-123",
        },
    )
    assert duplicate.status_code == 409
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "organization_slug": "same-slug",
            "email": "same@example.com",
            "password": "wrong-password",
        },
    )
    assert login.status_code == 401
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_database_rejects_cross_tenant_relations(test_engine) -> None:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        org_a = Organization(name="Org A", slug="db-org-a")
        org_b = Organization(name="Org B", slug="db-org-b")
        session.add_all([org_a, org_b])
        await session.flush()
        client_record = Client(org_id=org_a.id, name="Client A", email="a@example.com")
        project = ProjectOrder(
            org_id=org_a.id,
            client=client_record,
            project_key="PROJECT-A",
            name="Project A",
        )
        session.add_all([client_record, project])
        await session.flush()

        invalid_order = ProjectOrder(
            org_id=org_b.id,
            client_id=client_record.id,
            project_key="PROJECT-B",
            name="Invalid cross-tenant project",
        )
        session.add(invalid_order)
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

    async with factory() as session:
        org_a = Organization(name="Org A", slug="db-org-a-2")
        org_b = Organization(name="Org B", slug="db-org-b-2")
        session.add_all([org_a, org_b])
        await session.flush()
        client_record = Client(org_id=org_a.id, name="Client A", email="a2@example.com")
        project = ProjectOrder(
            org_id=org_a.id,
            client=client_record,
            project_key="PROJECT-A2",
            name="Project A2",
        )
        session.add_all([client_record, project])
        await session.flush()
        invalid_subscription = Subscription(
            org_id=org_b.id,
            project_id=project.id,
            name="Invalid cross-tenant subscription",
            amount="1.00",
            interval=BillingInterval.MONTHLY,
        )
        session.add(invalid_subscription)
        with pytest.raises(IntegrityError):
            await session.flush()
