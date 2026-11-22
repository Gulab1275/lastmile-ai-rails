"""add legacy_cnic_proposals table

Revision ID: 518bfe309c21
Revises: 417aeb409a15
Create Date: 2026-11-22 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '518bfe309c21'
down_revision = '417aeb409a15'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'legacy_cnic_proposals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('citizen_id', sa.String(), nullable=False),
        sa.Column('old_cnic', sa.String(length=15), nullable=False),
        sa.Column('proposed_cnic', sa.String(length=15), nullable=False),
        sa.Column('maker_officer_id', sa.String(), nullable=False),
        sa.Column('maker_notes', sa.Text(), nullable=False),
        sa.Column('physical_document_ref', sa.String(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('checker_supervisor_id', sa.String(), nullable=True),
        sa.Column('supervisor_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['citizen_id'], ['citizens.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legacy_cnic_proposals_citizen_id'), 'legacy_cnic_proposals', ['citizen_id'], unique=False)
    op.create_index(op.f('ix_legacy_cnic_proposals_physical_document_ref'), 'legacy_cnic_proposals', ['physical_document_ref'], unique=False)
    op.create_index(op.f('ix_legacy_cnic_proposals_status'), 'legacy_cnic_proposals', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_legacy_cnic_proposals_status'), table_name='legacy_cnic_proposals')
    op.drop_index(op.f('ix_legacy_cnic_proposals_physical_document_ref'), table_name='legacy_cnic_proposals')
    op.drop_index(op.f('ix_legacy_cnic_proposals_citizen_id'), table_name='legacy_cnic_proposals')
    op.drop_table('legacy_cnic_proposals')
