"""added the notification for the admin.

Revision ID: fb02ccc8445e
Revises: 7ff505d26b06
Create Date: 2025-05-21 09:56:21.948688

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb02ccc8445e'
down_revision = '7ff505d26b06'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('profile_update_requests')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('profile_update_requests',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('member_id', sa.INTEGER(), nullable=False),
    sa.Column('new_first_name', sa.VARCHAR(length=50), nullable=True),
    sa.Column('new_last_name', sa.VARCHAR(length=50), nullable=True),
    sa.Column('new_username', sa.VARCHAR(length=100), nullable=True),
    sa.Column('new_email', sa.VARCHAR(length=100), nullable=True),
    sa.Column('new_phone', sa.VARCHAR(length=20), nullable=True),
    sa.Column('new_password', sa.VARCHAR(length=200), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('approved_by', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['approved_by'], ['members.id'], ),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
