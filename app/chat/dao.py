from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from app.dao.base import BaseDAO
from app.chat.models import Chat, Message
from app.database import async_session_maker
from typing import List


class ChatsDAO(BaseDAO):
    model = Chat

    @classmethod
    async def get_user_chats(cls, user_id: int):
        """Получить все чаты пользователя"""
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .join(cls.model.participants)
                .where(cls.model.participants.any(id=user_id))
                .options(selectinload(cls.model.participants))
                .order_by(cls.model.created_at.desc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def create_chat(cls, name: str = None, participant_ids: List[int] = None):
        """Создать новый чат с участниками"""
        async with async_session_maker() as session:
            async with session.begin():
                # Создаем чат
                new_chat = cls.model(name=name)
                session.add(new_chat)
                await session.flush()  # Получаем ID чата

                # Добавляем участников
                from app.users.dao import UsersDAO
                for user_id in participant_ids:
                    user = await UsersDAO.find_one_or_none_by_id(user_id)
                    if user:
                        new_chat.participants.append(user)

                await session.commit()
                return new_chat

    @classmethod
    async def add_participant_to_chat(cls, chat_id: int, user_id: int):
        """Добавить участника в чат"""
        async with async_session_maker() as session:
            async with session.begin():
                chat = await session.get(cls.model, chat_id)
                user = await session.get(UsersDAO.model, user_id)

                if chat and user and user not in chat.participants:
                    chat.participants.append(user)

                await session.commit()


class MessagesDAO(BaseDAO):
    model = Message

    @classmethod
    async def get_chat_messages(cls, chat_id: int):
        """Получить сообщения чата"""
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .where(cls.model.chat_id == chat_id)
                .options(selectinload(cls.model.sender))
                .order_by(cls.model.created_at)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def add_message(cls, chat_id: int, sender_id: int, content: str):
        """Добавить сообщение в чат"""
        async with async_session_maker() as session:
            async with session.begin():
                new_message = cls.model(
                    chat_id=chat_id,
                    sender_id=sender_id,
                    content=content
                )
                session.add(new_message)
                await session.commit()
                return new_message