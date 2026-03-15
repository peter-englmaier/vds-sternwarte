"""Add observatory_reservation table

Revision ID: 9933de15e3ed
Revises: e7a47718181b
Create Date: 2026-03-15 13:14:47.544824

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9933de15e3ed'
down_revision = 'e7a47718181b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('observatory_reservation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('observatory_id', sa.Integer(), nullable=False),
    sa.Column('observation_request_id', sa.Integer(), nullable=False),
    sa.Column('reservation_max', sa.DateTime(), nullable=False),
    sa.Column('reservation_exp', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['observation_request_id'], ['observation_request.id'], name=op.f('fk_observatory_reservation_observation_request_id_observation_request')),
    sa.ForeignKeyConstraint(['observatory_id'], ['observatory.id'], name=op.f('fk_observatory_reservation_observatory_id_observatory')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_observatory_reservation')),
    sa.UniqueConstraint('date', name=op.f('uq_observatory_reservation_date'))
    )
    print("Please run: python -m datamigrations add_observatory_reservations")

def downgrade():
    op.drop_table('observatory_reservation')
