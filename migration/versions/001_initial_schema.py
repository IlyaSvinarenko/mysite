"""initial_schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Создаем таблицу users (если еще не существует)
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('hashed_password', sa.String(), nullable=False),
                    sa.Column('email', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Создаем таблицу chats
    op.create_table('chats',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Создаем таблицу chat_participants
    op.create_table('chat_participants',
                    sa.Column('chat_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('chat_id', 'user_id')
                    )

    # Создаем таблицу messages
    op.create_table('messages',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('chat_id', sa.Integer(), nullable=True),
                    sa.Column('sender_id', sa.Integer(), nullable=True),
                    sa.Column('content', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
                    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('messages')
    op.drop_table('chat_participants')
    op.drop_table('chats')
    op.drop_table('users')