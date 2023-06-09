"""added unique constraint to mac_id to device table

Revision ID: 2cd66c083aac
Revises: 079f3b383c35
Create Date: 2020-12-11 11:14:57.131180

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cd66c083aac'
down_revision = '079f3b383c35'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_device_mac_id', table_name='device')
    op.create_index(op.f('ix_device_mac_id'), 'device', ['mac_id'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_device_mac_id'), table_name='device')
    op.create_index('ix_device_mac_id', 'device', ['mac_id'], unique=False)
    # ### end Alembic commands ###
