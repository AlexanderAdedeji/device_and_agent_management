"""Add created_at and updated_at timestamps to all models

Revision ID: dd31b1ec0f9e
Revises: af4c8b6033d5
Create Date: 2020-11-27 10:52:36.167571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd31b1ec0f9e'
down_revision = 'af4c8b6033d5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('apipermission', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('apipermission', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('user', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('usertype', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('usertype', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('usertype', 'updated_at')
    op.drop_column('usertype', 'created_at')
    op.drop_column('user', 'updated_at')
    op.drop_column('user', 'created_at')
    op.drop_column('apipermission', 'updated_at')
    op.drop_column('apipermission', 'created_at')
    # ### end Alembic commands ###