"""add chat system

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
    # Создаем таблицу chats
    op.create_table('chats',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
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

    # Добавляем chat_id в messages
    op.add_column('messages', sa.Column('chat_id', sa.Integer(), nullable=True))

    # Создаем внешний ключ для chat_id
    op.create_foreign_key('messages_chat_id_fkey', 'messages', 'chats', ['chat_id'], ['id'])


def downgrade():
    # Удаляем внешний ключ
    op.drop_constraint('messages_chat_id_fkey', 'messages', type_='foreignkey')

    # Удаляем chat_id
    op.drop_column('messages', 'chat_id')

    # Удаляем таблицы
    op.drop_table('chat_participants')
    op.drop_table('chats')