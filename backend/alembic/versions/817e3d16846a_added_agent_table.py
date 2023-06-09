"""Added agent table

Revision ID: 817e3d16846a
Revises: 8c27593f685f
Create Date: 2021-05-02 17:27:35.408140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '817e3d16846a'
down_revision = '8c27593f685f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('agent',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('user_type_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['user_type_id'], ['usertype.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_email'), 'agent', ['email'], unique=True)
    op.create_index(op.f('ix_agent_id'), 'agent', ['id'], unique=False)
    op.drop_constraint('user_agent_id_fkey', 'user', type_='foreignkey')
    op.create_foreign_key(None, 'user', 'agent', ['agent_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.create_foreign_key('user_agent_id_fkey', 'user', 'user', ['agent_id'], ['id'])
    op.drop_index(op.f('ix_agent_id'), table_name='agent')
    op.drop_index(op.f('ix_agent_email'), table_name='agent')
    op.drop_table('agent')
    # ### end Alembic commands ###
