"""renamed field on users model from 'devices' to 'created_devices

Revision ID: 8bba44819b40
Revises: 882daf9ea29f
Create Date: 2020-11-27 12:44:30.040033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bba44819b40'
down_revision = '882daf9ea29f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
