"""drop api_keys owner foreign key constraint

Revision ID: 417aeb409a15
Revises: 396945dbc238
Create Date: 2026-11-21 23:52:42.261102

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "417aeb409a15"
down_revision: Union[str, None] = "396945dbc238"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE api_keys DROP CONSTRAINT IF EXISTS api_keys_owner_user_id_fkey")
    elif bind.dialect.name == "sqlite":
        # SQLite does not support ALTER TABLE DROP CONSTRAINT; safe no-op on SQLite
        pass
    else:
        try:
            op.drop_constraint("api_keys_owner_user_id_fkey", "api_keys", type_="foreignkey")
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "api_keys_owner_user_id_fkey",
            "api_keys",
            "users",
            ["owner_user_id"],
            ["id"],
        )
    elif bind.dialect.name == "sqlite":
        pass
    else:
        try:
            op.create_foreign_key(
                "api_keys_owner_user_id_fkey",
                "api_keys",
                "users",
                ["owner_user_id"],
                ["id"],
            )
        except Exception:
            pass
