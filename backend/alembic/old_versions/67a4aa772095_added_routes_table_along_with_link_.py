"""Added routes table, along with link table to support many-many queries

Revision ID: 67a4aa772095
Revises: 3369a7a2fde5
Create Date: 2020-11-23 16:26:20.072107

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67a4aa772095'
down_revision = '3369a7a2fde5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('route',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('route_name', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_route_id'), 'route', ['id'], unique=False)
    op.create_index(op.f('ix_route_route_name'), 'route', ['route_name'], unique=True)
    op.create_table('route_user_type',
    sa.Column('user_type_id', sa.Integer(), nullable=True),
    sa.Column('route_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['route_id'], ['route.id'], ),
    sa.ForeignKeyConstraint(['user_type_id'], ['usertype.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('route_user_type')
    op.drop_index(op.f('ix_route_route_name'), table_name='route')
    op.drop_index(op.f('ix_route_id'), table_name='route')
    op.drop_table('route')
    # ### end Alembic commands ###