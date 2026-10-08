"""Add session_version to user

Revision ID: a6d2c8f14b31
Revises: d68321ef59ce
Create Date: 2026-10-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6d2c8f14b31'
down_revision = 'd68321ef59ce'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('session_version', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade():
    op.drop_column('user', 'session_version')
