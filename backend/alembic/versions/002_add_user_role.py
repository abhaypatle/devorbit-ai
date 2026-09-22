"""Add role to users for role-aware workspaces."""

from alembic import op
import sqlalchemy as sa

revision = "002_add_user_role"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("role", sa.String(40), nullable=False, server_default="full_stack_developer"))


def downgrade():
    op.drop_column("users", "role")
