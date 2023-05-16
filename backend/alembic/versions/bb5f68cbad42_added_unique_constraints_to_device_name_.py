"""Added unique constraints to device name column

Revision ID: bb5f68cbad42
Revises: 8f23505131e1
Create Date: 2021-06-04 17:48:47.211554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb5f68cbad42'
down_revision = '8f23505131e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_device_name', table_name='device')
    op.create_index(op.f('ix_device_name'), 'device', ['name'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_device_name'), table_name='device')
    op.create_index('ix_device_name', 'device', ['name'], unique=False)
    # ### end Alembic commands ###