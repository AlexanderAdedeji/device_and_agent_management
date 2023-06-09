"""Ensured foreign key to user is not nullable

Revision ID: 3369a7a2fde5
Revises: a1872115b09d
Create Date: 2020-11-19 11:19:37.727810

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3369a7a2fde5'
down_revision = 'a1872115b09d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'user_type_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'user_type_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###
