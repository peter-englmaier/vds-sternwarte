"""Add role

Revision ID: 635e89d2919a
Revises: 
Create Date: 2024-08-04 19:41:58.434274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '635e89d2919a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rolename', sa.String(length=20), nullable=False),
    sa.Column('isAdmin', sa.Boolean(), nullable=False),
    sa.Column('isPowerUser', sa.Boolean(), nullable=False),
    sa.Column('isApprover', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('rolename')
    )
    op.create_table('role_group',
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['group.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], )
    )


def downgrade():
    op.drop_table('role_group')
    op.drop_table('role')
