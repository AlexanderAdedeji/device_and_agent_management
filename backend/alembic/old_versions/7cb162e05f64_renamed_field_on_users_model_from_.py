"""renamed field on users model from 'devices' to 'created_devices

Revision ID: 7cb162e05f64
Revises: df4fb92ad2b1
Create Date: 2020-11-27 12:48:59.025316

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7cb162e05f64'
down_revision = 'df4fb92ad2b1'
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
