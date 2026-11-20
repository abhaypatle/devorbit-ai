import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import (
    ApprovalAction,
    ApprovalRequest,
    AgentRun,
    Client,
    Organization,
    ProjectDocument,
    ProjectOrder,
    User,
    UserRole,
)


async def test_ai_records_enforce_org_and_project_foreign_keys(test_engine) -> None:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        org_a = Organization(name="Tenant A", slug="ai-tenant-a")
        org_b = Organization(name="Tenant B", slug="ai-tenant-b")
        session.add_all([org_a, org_b])
        await session.flush()
        user_a = User(
            org_id=org_a.id,
            email="admin@tenant-a.example.com",
            full_name="Admin A",
            password_hash="test-hash",
            role=UserRole.ADMIN,
        )
        user_b = User(
            org_id=org_b.id,
            email="admin@tenant-b.example.com",
            full_name="Admin B",
            password_hash="test-hash",
            role=UserRole.ADMIN,
        )
        client = Client(org_id=org_a.id, name="Client A", email="client@tenant-a.example.com")
        session.add_all([user_a, user_b, client])
        await session.flush()
        project = ProjectOrder(
            org_id=org_a.id,
            client_id=client.id,
            project_key="AI-TENANT-A",
            name="Tenant A project",
        )
        session.add(project)
        await session.commit()
        tenant_a_id = org_a.id
        tenant_b_id = org_b.id
        user_a_id = user_a.id
        user_b_id = user_b.id
        project_id = project.id

    async with factory() as session:
        session.add(
            ProjectDocument(
                org_id=tenant_b_id,
                project_id=project_id,
                uploaded_by_id=user_b_id,
                title="Cross-tenant document",
                filename="cross.md",
                content_type="text/markdown",
                storage_key="cross-tenant/document",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

    async with factory() as session:
        session.add(
            AgentRun(
                org_id=tenant_b_id,
                project_id=project_id,
                requested_by_id=user_b_id,
                mode="scope",
                input_text="Cross-tenant request",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

    async with factory() as session:
        run = AgentRun(
            org_id=tenant_a_id,
            project_id=project_id,
            requested_by_id=user_a_id,
            mode="scope",
            input_text="Tenant A request",
        )
        session.add(run)
        await session.commit()
        run_id = run.id

    async with factory() as session:
        session.add(
            ApprovalRequest(
                org_id=tenant_a_id,
                project_id=project_id,
                agent_run_id=run_id,
                action=ApprovalAction.CHANGE_REQUEST_QUOTE,
                idempotency_key="cross-tenant-reviewer-key",
                reviewer_id=user_b_id,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
